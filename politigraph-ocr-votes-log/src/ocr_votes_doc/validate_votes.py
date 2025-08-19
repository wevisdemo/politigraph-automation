from typing import List, Dict, Any
import pandas as pd

def validate_votes(
    votes_df: pd.DataFrame,
    validate_data: Dict[str, int],
    vote_options:List[str]=["เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"],
    vote_option_column:str='ผลการลงคะแนน'
) -> bool:
    # จำนวนผู้เข้าร่วมประชุม
    attendance_count = sum([
        validate_data.get(category, 0) for category in vote_options
    ])
    
    if vote_option_column not in votes_df.columns: # if the column does not exist
        return False
    
    attended_votes_df = votes_df.loc[
        votes_df[vote_option_column] != "ลา / ขาดลงมติ"
    ]
    
    # Check attendace
    if len(attended_votes_df.index) != attendance_count:
        return False
    
    # Check option counts
    for option in vote_options:
        if len(attended_votes_df.loc[
            attended_votes_df[vote_option_column] == option
        ]) != validate_data.get(option, -1):
            return False
    return True