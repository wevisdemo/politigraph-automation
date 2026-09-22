from .vote_log import VoteLog

def get_vote_log_object(pdf_path: str) -> VoteLog:
    # Instantiate new VoteLog
    vote_log = VoteLog(pdf_path)
    return vote_log

def ocr_votes_doc(pdf_path: str) -> dict[str, str|dict|list]:
    
    # Instantiate new VoteLog
    vote_log = VoteLog(pdf_path)
    return vote_log.to_dict()