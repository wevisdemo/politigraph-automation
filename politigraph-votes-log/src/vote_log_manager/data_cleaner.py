import re

import pandas as pd
from rapidfuzz import distance

from poliquery import get_political_parties

from .prefixes_helper import get_thai_name_prefixes
from .text_helper import correct_typo


def get_text_number_in_text(text: str) -> str:

    number_text = re.sub(r"\D", "", str(text)).strip()
    return number_text

def normalize_vote_option(
    option_text: str,
    vote_option_index: dict[str, list[str]] = {
        'เห็นด้วย': ['เห็นชอบ', 'รับหลักการ', 'เห็นด้วย'],
        'ไม่เห็นด้วย': ['ไม่เห็นชอบ', 'ไม่รับหลักการ', 'ไม่เห็นด้วย'],
        'งดออกเสียง': ['งดออกเสียง', 'งด'],
        'ไม่ลงคะแนนเสียง': ['ไม่ลงคะแนน', 'ไม่ลงคะแนนเสียง', 'ไม่ประสงค์ลงคะแนน'],
        'ลา / ขาดลงมติ': ['ลา', 'ขาด', 'ขาดลงมติ', 'ขาดประชุม'],
    },
    critical_prefixes: tuple[str, ...] = ("ไม่", "งด")
) -> str:
    option_text = option_text.strip()

    # --- Handle dash / absent marker early ---
    # Catches standard hyphen (-), en-dash (–), and em-dash (—)
    if option_text in ("-", "–", "—", ""):
        return "ลา / ขาดลงมติ"

    # 1. Detect if the text starts with a critical prefix ('ไม่' or 'งด')
    active_prefix = next((p for p in critical_prefixes if option_text.startswith(p)), None)

    # 2. Filter category candidates by prefix to isolate polarity
    if active_prefix:
        filtered_index = {
            cat: phrases for cat, phrases in vote_option_index.items()
            if cat.startswith(active_prefix)
        }
    else:
        filtered_index = {
            cat: phrases for cat, phrases in vote_option_index.items()
            if not any(cat.startswith(p) for p in critical_prefixes)
        }

    # Fallback to all categories if no match was found
    target_index = filtered_index if filtered_index else vote_option_index

    # 3. Calculate the closest distance in each category (lower is better)
    matched_option_index = {}
    for _option, _options_text_list in target_index.items():
        normalized_distances = [
            distance.Levenshtein.distance(option_text, _op) / max(len(option_text), len(_op))
            if max(len(option_text), len(_op)) > 0 else 0.0
            for _op in _options_text_list
        ]
        matched_option_index[_option] = min(normalized_distances)

    # 4. Pick the category with the lowest distance (best match)
    matched_option = min(matched_option_index, key=lambda k: matched_option_index[k])

    return matched_option

def remove_name_prefix(name: str) -> str:
    prefixes = get_thai_name_prefixes()
    # Try load prefix from politigraph
    try:
        from poliquery import get_politician_prefixes
        prefixes.extend(get_politician_prefixes())
    except Exception as e:
        print(f"failed to connect to politigraph : {e}")

    # Sort unique prefixes by length in descending order
    sorted_prefixes = sorted(set(prefixes), key=len, reverse=True)

    # Escape each prefix in case it contains regex special characters (e.g. '.')
    pattern = r"^(" + "|".join(re.escape(p) for p in sorted_prefixes) + r")"

    removed_prefix = re.sub(pattern, "", name).strip()

    return removed_prefix

def correct_thai_name(name: str) -> str:

    # Try load names from politigraph
    try:
        from poliquery import get_representative_members_name
        representatives = get_representative_members_name()
        names_list = [
            person.get('name', '') for person in representatives
        ]
        return correct_typo(name, names_list)
    except:
        return name

def clean_voter_affiliation(voter_affiliation: str) -> str:
    
    cleaned_text = str(voter_affiliation)
    
    # Clean non Thai characters
    cleaned_text = re.sub(r"[^\u0e01-\u0e4c]", "", cleaned_text)
    
    # Clean วรรณยุกต์ at the start of the text
    cleaned_text = re.sub(r"^([\u0e30-\u0e3a]|[\u0e47-\u0e4e])", "", cleaned_text)
    
    # Clean พรรค
    cleaned_text = re.sub(r"^[\u0e01-\u0e2e]รรค", "", cleaned_text)
    
    # Match with closest party
    # Query all political party
    political_parties = get_political_parties()
    party_names = [p.get('name', '') for p in political_parties]
    cleaned_text = correct_typo(
        typo_text=cleaned_text,
        correct_texts_list=party_names + ['สมาชิกวุฒิสภา']
    )
    
    return cleaned_text

def clean_votes_df(votes_df: pd.DataFrame) -> pd.DataFrame:

    # Check columns
    assert all(col in votes_df.columns for col in [
        "ลำดับที่", "เลขที่บัตร", "ชื่อ - สกุล", "ชื่อสังกัด", "ผลการลงคะแนน"
    ])

    df = votes_df.copy()

    # Clean numbers
    df["ลำดับที่"] = df["ลำดับที่"].astype(str)
    df["ลำดับที่"] = df["ลำดับที่"].apply(get_text_number_in_text)
    df["เลขที่บัตร"] = df["เลขที่บัตร"].apply(get_text_number_in_text)

    # Clean name
    df.loc[:, "ชื่อ - สกุล"] = df["ชื่อ - สกุล"].apply(remove_name_prefix) # remove prefix
    df.loc[:, "ชื่อ - สกุล"] = df["ชื่อ - สกุล"].apply(correct_thai_name) # correct name
    
    # Clean voter affiliation
    df["ชื่อสังกัด"] = df["ชื่อสังกัด"].apply(clean_voter_affiliation) # correct name

    # Clean vote options
    df.loc[:, "ผลการลงคะแนน"] = df["ผลการลงคะแนน"].apply(
        lambda vote_opt: normalize_vote_option(vote_opt)
    )

    # Clean any row with multiple empty strings
    df = df[(df == "").sum(axis=1) < 2]

    return df
