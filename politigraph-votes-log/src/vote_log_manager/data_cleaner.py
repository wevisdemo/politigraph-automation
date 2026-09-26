import re
import pandas as pd
from rapidfuzz import distance
from .text_helper import correct_typo
from .prefixes_helper import get_thai_name_prefixes

def get_text_number_in_text(text: str) -> str:
    
    number_text = re.sub(r"\D", "", text).strip()
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
    except:
        pass
    
    removed_prefix = re.sub(
        r"^(" + "|".join(prefixes) + r")",
        "",
        name
    ).strip()
    
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

def clean_votes_df(votes_df: pd.DataFrame) -> pd.DataFrame:
    
    # Check columns
    assert all(col in votes_df.columns for col in [
        "ลำดับที่", "เลขที่บัตร", "ชื่อ - สกุล", "ชื่อสังกัด", "ผลการลงคะแนน"
    ])
    
    df = votes_df.copy()
    
    # Clean numbers
    df.loc[:, "ลำดับที่"] = df["ลำดับที่"].apply(get_text_number_in_text)
    df.loc[:, "เลขที่บัตร"] = df["ลำดับที่"].apply(get_text_number_in_text)
    
    # Clean name
    df.loc[:, "ชื่อ - สกุล"] = df["ชื่อ - สกุล"].apply(remove_name_prefix) # remove prefix
    df.loc[:, "ชื่อ - สกุล"] = df["ชื่อ - สกุล"].apply(correct_thai_name) # correct name
    
    # Clean vote options
    df.loc[:, "ผลการลงคะแนน"] = df["ผลการลงคะแนน"].apply(
        lambda vote_opt: normalize_vote_option(vote_opt)
    )
    
    # Clean any row with multiple empty strings
    df = df[(df == "").sum(axis=1) < 2]
    
    return df
    