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
    vote_option_index: dict[str, list[str]]= {
        'เห็นด้วย': ['เห็นชอบ', 'รับหลักการ', 'เห็นด้วย'],
        'ไม่เห็นด้วย': ['ไม่เห็นชอบ', 'ไม่รับหลักการ', 'ไม่เห็นด้วย'],
        'งดออกเสียง': ['งดออกเสียง', 'งด'],
        'ไม่ลงคะแนนเสียง': ['ไม่ลงคะแนน', 'ไม่ลงคะแนนเสียง', 'ไม่ประสงค์ลงคะแนน'],
    }
) -> str:
    
    # Get closest option
    matched_option_index = {}
    for _option, _options_text_list in vote_option_index.items():
        matched_option_index[_option] = max(
            distance.Levenshtein.distance(option_text, _op) for _op in _options_text_list
        )
        
    matched_option = max(matched_option_index, key=lambda k: matched_option_index[k])
    
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
    
    # TODO update poliquery to get name easier
    return name
    
    # Try load names from politigraph
    try: 
        from poliquery import get_politician_name_index
        name_index = get_politician_name_index()
    except:
        return name
    
    names_list = list(name_index.keys())
        
    return correct_typo(name, names_list)

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
    df.loc[:, "ผลการลงคะแนน"] = df["ผลการลงคะแนน"].apply(normalize_vote_option)
    
    # Clean any row with multiple empty strings
    df = df[(df == "").sum(axis=1) < 2]
    
    return df
    