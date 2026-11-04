from pathlib import Path
from typing import Literal

from .vote_log import VoteLog


def get_vote_log_object(pdf_path: str|Path, classification_type: Literal['MP', 'SENATE']='MP') -> VoteLog:
    # Instantiate new VoteLog
    vote_log = VoteLog(pdf_path, classification_type=classification_type)
    return vote_log

def ocr_votes_doc(pdf_path: str|Path, classification_type: Literal['MP', 'SENATE']='MP') -> dict[str, str|dict|list]:

    # Instantiate new VoteLog
    vote_log = VoteLog(pdf_path, classification_type=classification_type)
    vote_log.get_votes()
    return vote_log.to_dict()
