from typing import List
import pandas as pd

def update_extra_votes(
    votes_df: pd.DataFrame,
    extra_votes_df: pd.DataFrame,
    vote_options:List[str]=["เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"],
    name_colum:str='ชื่อ - สกุล',
    vote_option_column:str='ผลการลงคะแนน'
) -> pd.DataFrame:
    
    df = votes_df.copy()
    
    # Filter out invalid vote options
    filtered_extra_votes_df = extra_votes_df.loc[
        extra_votes_df[vote_option_column].isin(vote_options)
    ]
    
    name_option_dict = filtered_extra_votes_df.set_index(name_colum)[vote_option_column].to_dict()
    for name, option in name_option_dict.items():
        df.loc[df[name_colum] == name, vote_option_column] = option
        
    # Add any vote with non repeat name
    new_votes_df = extra_votes_df[~(extra_votes_df[name_colum].isin(df[name_colum].unique()))]
    df = pd.concat(
        [df, new_votes_df],
        ignore_index=True
    )
    
    return df