import os
from pathlib import Path
import pandas as pd
from poliquery import add_votes_to_vote_event

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
        vote_logs=vote_logs, # type: ignore
    )
    