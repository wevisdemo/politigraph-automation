import re
import pandas as pd
import numpy as np

from .typo_cleaner import correct_typo
from .politigraph_data_loader import get_politician_names, get_politocal_party_names

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
    df['ผลการลงคะแนน'] = df['ผลการลงคะแนน'].apply(
        lambda x: "ลา / ขาดลงมติ" if x == "-" else correct_typo(
            x, 
            vote_options_texts,
            similarity_threshold=80
        )
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
    
    # Remove name prefix
    # TODO change from hardcode to load name_prefix from somewhere else
    name_prefixes = [
        "นาย", "นาง", "นางสาว",  

        "ดร.", "ศาสตราจารย์", "ศาสตราจารย์ ดร.", "ศ.ดร.",
        "รองศาสตราจารย์", "รศ.", "ผู้ช่วยศาสตราจารย์", "ผศ.",

        "พลเอก", "พลโท", "พลตรี", 
        "พันเอก", "พันโท", "พันตรี", 
        "ร้อยเอก", "ร้อยโท", "ร้อยตรี",
        "ว่าที่พันเอก", "ว่าที่พันเอกหญิง", 
        "ว่าที่พันโท", "ว่าที่พันโทหญิง", 
        "ว่าที่พันตรี", "ว่าที่พันตรีหญิง",
        "ว่าที่ร้อยเอก", "ว่าที่ร้อยเอกหญิง", 
        "ว่าที่ร้อยโท", "ว่าที่ร้อยโทหญิง", 
        "ว่าที่ร้อยตรี", "ว่าที่ร้อยตรีหญิง",
        "จ่าสิบเอก", "จ่าสิบโท", "จ่าสิบตรี",
        "สิบเอก", "สิบโท", "สิบตรี",

        "พล.อ.", "พล.ท.", "พล.ต.",
        "พ.อ.", "พ.ท.", "พ.ต.",
        "ร.อ.", "ร.ท.", "ร.ต.",
        "จ.ส.อ.", "จ.ส.ท.", "จ.ส.ต.",
        "ส.อ.", "ส.ท.", "ส.ต.",

        "พลตำรวจเอก", "พลตำรวจโท", "พลตำรวจตรี", 
        "พันตำรวจเอก", "พันตำรวจโท", "พันตำรวจตรี", 
        "ร้อยตำรวจเอก", "ร้อยตำรวจโท", "ร้อยตำรวจตรี",
        "จ่าสิบตำรวจ", "สิบตำรวจเอก", "สิบตำรวจโท", "สิบตำรวจตรี",

        "พล.ต.อ.", "พล.ต.ท.", "พล.ต.ต.",
        "พ.ต.อ.", "พ.ต.ท.", "พ.ต.ต.",
        "ร.ต.อ.", "ร.ต.ท.", "ร.ต.ต.",
        "จ.ส.ต.", "ส.ต.อ.", "ส.ต.ท.", "ส.ต.ต."

        # Medical
        "นายแพทย์", "นพ.", "แพทย์หญิง", "พญ.",

        # Navy Ranks (Full)
        "พลเรือเอก", "พลเรือโท", "พลเรือตรี",
        "นาวาเอก", "นาวาโท", "นาวาตรี",
        "เรือเอก", "เรือโท", "เรือตรี",
        "พันจ่าเอก", "พันจ่าโท", "พันจ่าตรี",
        "จ่าเอก", "จ่าโท", "จ่าตรี",

        # Navy Ranks (Abbreviated)
        "พล.ร.อ.", "พล.ร.ท.", "พล.ร.ต.",
        "น.อ.", "น.ท.", "น.ต.",
        "ร.อ.", "ร.ท.", "ร.ต.",
        "พ.จ.อ.", "พ.จ.ท.", "พ.จ.ต.",
        "จ.อ.", "จ.ท.", "จ.ต.",

        # Acting Navy Ranks
        "ว่าที่นาวาเอก", "ว่าที่นาวาเอกหญิง",
        "ว่าที่นาวาโท", "ว่าที่นาวาโทหญิง",
        "ว่าที่นาวาตรี", "ว่าที่นาวาตรีหญิง",
        "ว่าที่เรือเอก", "ว่าที่เรือเอกหญิง",
        "ว่าที่เรือโท", "ว่าที่เรือโทหญิง",
        "ว่าที่เรือตรี", "ว่าที่เรือตรีหญิง",
        # Optional: Abbreviated Acting Navy Ranks (less common in formal lists)
        "ว่าที่ น.อ.", "ว่าที่ น.อ.หญิง",
        "ว่าที่ น.ท.", "ว่าที่ น.ท.หญิง",
        "ว่าที่ น.ต.", "ว่าที่ น.ต.หญิง",
        "ว่าที่ ร.อ.", "ว่าที่ ร.อ.หญิง",
        "ว่าที่ ร.ท.", "ว่าที่ ร.ท.หญิง",
        "ว่าที่ ร.ต.", "ว่าที่ ร.ต.หญิง",


        # Acting Police Ranks
        "ว่าที่พลตำรวจเอก", "ว่าที่พลตำรวจเอกหญิง",
        "ว่าที่พลตำรวจโท", "ว่าที่พลตำรวจโทหญิง",
        "ว่าที่พลตำรวจตรี", "ว่าที่พลตำรวจตรีหญิง",
        "ว่าที่พันตำรวจเอก", "ว่าที่พันตำรวจเอกหญิง",
        "ว่าที่พันตำรวจโท", "ว่าที่พันตำรวจโทหญิง",
        "ว่าที่พันตำรวจตรี", "ว่าที่พันตำรวจตรีหญิง",
        "ว่าที่ร้อยตำรวจเอก", "ว่าที่ร้อยตำรวจเอกหญิง",
        "ว่าที่ร้อยตำรวจโท", "ว่าที่ร้อยตำรวจโทหญิง",
        "ว่าที่ร้อยตำรวจตรี", "ว่าที่ร้อยตำรวจตรีหญิง",
        # Optional: Abbreviated Acting Police Ranks (less common in formal lists)
        "ว่าที่ พล.ต.อ.", "ว่าที่ พล.ต.อ.หญิง",
        "ว่าที่ พล.ต.ท.", "ว่าที่ พล.ต.ท.หญิง",
        "ว่าที่ พล.ต.ต.", "ว่าที่ พล.ต.ต.หญิง",
        "ว่าที่ พ.ต.อ.", "ว่าที่ พ.ต.อ.หญิง",
        "ว่าที่ พ.ต.ท.", "ว่าที่ พ.ต.ท.หญิง",
        "ว่าที่ พ.ต.ต.", "ว่าที่ พ.ต.ต.หญิง",
        "ว่าที่ ร.ต.อ.", "ว่าที่ ร.ต.อ.หญิง",
        "ว่าที่ ร.ต.ท.", "ว่าที่ ร.ต.ท.หญิง",
        "ว่าที่ ร.ต.ต.", "ว่าที่ ร.ต.ต.หญิง",
    ]
    name_prefixes.extend(prefixes)  # Add any additional prefixes from the input
    df['ชื่อ - สกุล'] = df['ชื่อ - สกุล'].apply(
        lambda name: min(
            [re.sub(r"^" + prefix, "", name).strip() for prefix in name_prefixes],
            key=len
        )
    )
    
    politician_names = get_politician_names()
    if len(politician_names) == 0: # No politician names got returned back
        return df
    df['ชื่อ - สกุล'] = df['ชื่อ - สกุล'].apply(
        lambda name: correct_typo(name, politician_names).strip()
    )
    
    return df

def clean_df_political_party(
    df_original: pd.DataFrame
):
    df = df_original.copy()
    
    # Remove anything before the word 'พรรค'
    df['ชื่อสังกัด'] = df['ชื่อสังกัด'].apply(
        lambda name: re.sub(r".*?(?=พรรค)", "", name)
    )
    
    parties_name = get_politocal_party_names()
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

def clean_votelog_df(df_original: pd.DataFrame) -> pd.DataFrame:
    df = df_original.copy()
    
    # Clean numbers
    df = clean_df_number(df)
    
    # Clean double rows name
    df = merged_double_rows_name(df)
    
    # Clean vote options
    df = clean_df_vote_options(df)
    
    # Clean Politician Name
    df = clean_df_politician_name(df)
    
    # Clean Political Party Name
    df = clean_df_political_party(df)
    
    # Clean rows with 3 or more empty values
    df = remove_rows_with_many_empty_values(df)
    
    return df
