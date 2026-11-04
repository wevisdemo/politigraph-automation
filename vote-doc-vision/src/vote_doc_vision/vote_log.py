from pathlib import Path
from typing import Literal

import pandas as pd

from .constants import COLUMNS_INDEX_TH
from .doc_loader import load_pdf_images
from .vote_log_info_helper import extract_vote_log_info, extract_votes


class VoteLog:

    def __init__(
        self,
        pdf_file_path: str|Path,
        classification_type: Literal['MP', 'SENATE']='MP'
    ):
        self.page_images = load_pdf_images(pdf_file_path)

        # Extract info from first page
        vote_log_info = extract_vote_log_info(
            page_img=self.page_images[0],
            classification_type=classification_type
        )

        self.vote_event_title = vote_log_info.get('title', '')
        self.classification = vote_log_info.get('classification')

        self.vote_date = vote_log_info.get('vote_date')

        self.attendance_count = vote_log_info['attendance_count']
        self.agree_count = vote_log_info['agree_count']
        self.disagree_count = vote_log_info['disagree_count']
        self.abstain_count = vote_log_info['abstain_count']
        self.novote_count = vote_log_info['novote_count']

        self.is_ocr = False
        self.votes = vote_log_info.get('votes', [])

    def get_title(self) -> str:
        return self.vote_event_title # type: ignore

    def get_classification(self) -> str:
        return self.classification # type: ignore

    def get_start_date(self) -> str:
        return self.vote_date # type: ignore

    def get_vote_count(self) -> dict:
        option_count = {
            'attendance_count': self.attendance_count,
            'agree_count': self.agree_count,
            'disagree_count': self.disagree_count,
            'abstain_count': self.abstain_count,
            'novote_count': self.novote_count,
        }
        return option_count

    def get_votes(self):
        if self.is_ocr:
            return self.votes

        votes = self.votes
        for page in self.page_images[1:]:
            _extracted_vote = extract_votes(page)
            votes.extend(_extracted_vote) # type: ignore

        self.votes = votes
        self.is_ocr = True

        return self.votes

    def to_dict(self) -> dict:
        vote_title = self.vote_event_title
        vote_info = {
            'date': self.vote_date,
            'option_count': {
                'attendance_count': self.attendance_count,
                'agree_count': self.agree_count,
                'disagree_count': self.disagree_count,
                'abstain_count': self.abstain_count,
                'novote_count': self.novote_count,
            }
        }

        votes_data = self.votes

        return {
            "title": vote_title,
            "classification": self.classification,
            "vote_info": vote_info,
            "votes_data": votes_data,
        }

    def get_votes_df(self) -> pd.DataFrame:
        votes_df = pd.DataFrame(self.votes)
        votes_df.rename(columns=COLUMNS_INDEX_TH, inplace=True)
        return votes_df
