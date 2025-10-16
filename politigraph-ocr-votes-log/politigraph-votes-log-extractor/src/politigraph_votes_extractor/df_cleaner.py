import re
import pandas as pd
import numpy as np

from .typo_cleaner import correct_typo
from thai_name_normalizer import remove_thai_name_prefix
from poliquery import get_politician_prefixes, get_political_parties_name, get_people_in_party

def merged_double_rows_name(
    df_original: pd.DataFrame,
    specific_col: str="ชื่อ - สกุล"
) -> pd.DataFrame:
    
    df = df_original.copy()
    
    # Remove missing vote options
    df['ผลการลงคะแนน'] = df['ผลการลงคะแนน'].apply(
        lambda x: "" if len(x)<5 else x
    )
    
    # Replace empty string with NaN
    df.replace("", np.nan, inplace=True)

    other_cols = [col for col in df.columns if col != specific_col]

    # Identify rows that should be merged upwards (value in specific_col, NaNs elsewhere)
    is_merge_candidate_row = df[other_cols].isna().all(axis=1) & df[specific_col].notna()

    # Create a grouper. A new group starts when a row is NOT a merge_candidate_row.
    # The cumsum() of this boolean series effectively creates group IDs.
    # (True becomes 1, False becomes 0. cumsum() increments on True)
    group_key = (~is_merge_candidate_row).cumsum()

    # Define an aggregation function for each group
    def aggregate_rows(group):
        # The first row of the group contains the base values for other_cols
        first_row_data = group.iloc[0].copy()

        # Concatenate all non-NaN values from the specific_col within this group
        # Ensure values are strings before concatenation.
        # Using dropna() before astype(str) avoids "nan" string if specific_col had NaN.
        concatenated_specific_value = " ".join(group[specific_col].dropna().astype(str))

        first_row_data[specific_col] = concatenated_specific_value
        return first_row_data

    # Group by the key and apply the aggregation
    df_groupby_result = df.groupby(group_key, sort=False).apply(aggregate_rows)

    # The group_key might become the index, so reset it.
    df_groupby_result = df_groupby_result.reset_index(drop=True)
    
    # Fill NaN back to empty string
    df_groupby_result = df_groupby_result.fillna("")
    return df_groupby_result

    
def clean_number_text(number_str: str) -> str:
    matched_num = [num.strip() for num in re.findall(r"\d{1,}", number_str)]
    if len(matched_num) > 0:
        return str(max(
            matched_num,
            key=len
        ))
    return ""

def clean_df_number(
    df_original: pd.DataFrame,
    columns=['ลําดับที่', 'เลขที่บัตร']
) -> pd.DataFrame:
    df = df_original.copy()
    df.fillna("", inplace=True)
    for col in columns:
        df[col] = df[col].apply(lambda x: clean_number_text(x))
        
    return df

def clean_df_vote_options(
    df_original: pd.DataFrame,
    vote_options_texts=["เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"]
):
    df = df_original.copy()
    
    # Clean special characters out of name
    df['ผลการลงคะแนน'] = df['ผลการลงคะแนน'].apply(
        lambda name: re.sub(r"[^\u0E00-\u0E7F\s]", "", name).strip()
    )
    
    # change empty option to '-'
    df['ผลการลงคะแนน'] = df['ผลการลงคะแนน'].apply(
        lambda x: "-" if len(x) < 5 else x
    )
    # Clean typo
    def clean_vote_option_typo(text: str) -> str:
        if text == "-":
            return "-"
        correct_text = correct_typo(text, vote_options_texts, similarity_threshold=80)
        if correct_text in vote_options_texts:
            return correct_text
        # if not corrected, try to replace some common typos characters
        replacements = {
            r"ท": "ห",
            r"ด้าย": "ด้วย",
            r"(?<=น)ด(้)?าย": "ด้วย",
        }
        for typo, correct in replacements.items():
            text = re.sub(typo, correct, text)
        return correct_typo(text, vote_options_texts, similarity_threshold=80)
        
    df['ผลการลงคะแนน'] = df['ผลการลงคะแนน'].apply(clean_vote_option_typo)
    df['ผลการลงคะแนน'] = df['ผลการลงคะแนน'].apply(
        lambda x: "ลา / ขาดลงมติ" if x == "-" else x
    )
    
    return df

def clean_df_politician_name(
    df_original: pd.DataFrame,
    prefixes: list = []
):
    df = df_original.copy()
    
    # Clean special characters out of name
    df['ชื่อ - สกุล'] = df['ชื่อ - สกุล'].apply(
        lambda name: re.sub(r"[^\u0E00-\u0E7F\s]", "", name).strip()
    )
    
    # Clean typo in prefix
    perfix_pattern = {
        "ว่าที่": r"^วาที่", # handle specific case of ว่าที่..
        "ผู้ช่วยศาสตราจารย์": r"^ผูชวยศาสตราจารย"
    }
    def clean_prefixes_typo(name):
        new_name = name
        for correct_prefix, pattern in perfix_pattern.items():
            new_name = re.sub(pattern, correct_prefix, new_name)
        return new_name
    
    # Load prefixes from politigraph
    prefixes = get_politician_prefixes()
    # Remove name prefix
    df['ชื่อ - สกุล'] = df['ชื่อ - สกุล'].apply(clean_prefixes_typo) # clean prefix typo
    df['ชื่อ - สกุล'] = df['ชื่อ - สกุล'].apply(lambda name: remove_thai_name_prefix(
        name=name,
        prefixes=prefixes
    ))
    
    # Load politicians name & clean them
    parties_name = df['ชื่อสังกัด'].to_list()
    politicians_name = []
    for party_name in parties_name:
        politicians_name.extend([d['name'] for d in get_people_in_party(party_name)])
    if len(politicians_name) == 0: # No politician names got returned back
        return df
    df['ชื่อ - สกุล'] = df['ชื่อ - สกุล'].apply(
        lambda name: correct_typo(name, politicians_name).strip()
    )
    
    return df

def clean_df_political_party(
    df_original: pd.DataFrame
):
    df = df_original.copy()
    
    # Remove anything before and the word 'พรรค'
    df['ชื่อสังกัด'] = df['ชื่อสังกัด'].apply(
        lambda name: re.sub(r".*?พรรค", "", name)
    )
    
    parties_name = get_political_parties_name()
    if len(parties_name) == 0: # No parties names got returned back
        return df
    df['ชื่อสังกัด'] = df['ชื่อสังกัด'].apply(
        lambda name: correct_typo(name, parties_name)
    )
    
    return df

def remove_rows_with_many_empty_values(
    df_original: pd.DataFrame,
    threshold: int = 3
) -> pd.DataFrame:
    df = df_original.copy()
    
    is_empty_or_nan = (df.isna()) | (df == '')

    # Count the number of True values (empty/NaN) per row
    empty_counts_per_row = is_empty_or_nan.sum(axis=1)
    
    rows_to_keep_mask = empty_counts_per_row <= threshold
    return df[rows_to_keep_mask]

def clean_votelog_df(
    df_original: pd.DataFrame, 
) -> pd.DataFrame:
    df = df_original.copy()
    
    # Clean numbers
    df = clean_df_number(df)
    
    # Clean double rows name
    df = merged_double_rows_name(df)
    
    # Clean vote options
    df = clean_df_vote_options(df)
    
    # Clean Political Party Name
    df = clean_df_political_party(df)
    
    # Clean Politician Name
    df = clean_df_politician_name(df)
    
    # Clean rows with 3 or more empty values
    df = remove_rows_with_many_empty_values(df)
    
    return df

def clean_extra_votes_df(
    df_original: pd.DataFrame, 
) -> pd.DataFrame:
    df = df_original.copy()
    
    # Clean vote options
    df = clean_df_vote_options(df)
    
    # Clean Politician Name
    df = clean_df_politician_name(df)
    
    return df
