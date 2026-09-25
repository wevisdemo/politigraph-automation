import os
from pathlib import Path
import pandas as pd
from poliquery import add_votes_to_vote_event, update_vote_event_validation_data

def add_votes(
    vote_event_id: str,
    votes: pd.DataFrame|str|Path
) -> None:
    
    votes_df = None
    csv_file_path = None
    
    # Check path
    if isinstance(votes, pd.DataFrame):
        votes_df = votes.copy()
    elif isinstance(votes, str) | isinstance(votes, Path):
        csv_file_path = votes
        if isinstance(votes, str):
            csv_file_path = Path(votes)
        assert os.path.exists(csv_file_path)
        # Load to df
        votes_df = pd.read_csv(csv_file_path)
    
    assert votes_df is not None
    vote_logs = votes_df.to_dict('records')
    # Add votes to voteEvent
    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        vote_logs=vote_logs[::-1], # type: ignore
    )
    
def update_vote_counts(
    vote_event_id: str,
    vote_count_data: dict[str, int]
) -> None:
    
    # Contruct validation_data keys
     validation_data = {
         "เห็นด้วย": vote_count_data.get('agree_count', -1),
         "ไม่เห็นด้วย": vote_count_data.get('disagree_count', -1),
         "งดออกเสียง": vote_count_data.get('abstain_count', -1),
         "ไม่ลงคะแนนเสียง": vote_count_data.get('novote_count', -1),
     }
     
     update_vote_event_validation_data(
         vote_event_id=vote_event_id,
         validation_data=validation_data
     )