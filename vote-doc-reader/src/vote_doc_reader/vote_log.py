from typing import Any, Hashable
import pandas as pd
from tqdm.auto import tqdm
from .doc_loader import load_pdf_images
from .page_img_helper import (
    get_title_section, 
    get_info_section, get_info_data_images, 
    get_table_image, get_rows_images_in_table, 
    get_extra_votes_images
)
from .text_ocr import detect_and_read_text, read_text_in_row_data, read_info_text
from .constants import COLUMNS_INDEX_TH

class VoteLog():
    
    def __init__(
        self,
        pdf_file_path: str
    ):
        self.page_images = load_pdf_images(pdf_file_path)
        
        self.vote_event_title = None
        
        self.vote_date = None
        self.vote_options_count = None
        
        self.votes_data = None
        
    def get_vote_event_title(self):
        if self.vote_event_title is None:
            # Get first page
            first_page = self.page_images[0]
            title_section = get_title_section(first_page)
            
            self.vote_event_title = detect_and_read_text(title_section, separator=" ", use_typhoon=True)
        
        return self.vote_event_title
    
    def get_vote_info(self):
        if self.vote_options_count is None or self.vote_date is None:
            # Get first page
            first_page = self.page_images[0]
            info_section_image = get_info_section(first_page)
            info_data_imges = get_info_data_images(info_section_image)
            
            info_data = read_info_text(info_data_imges)
            
            self.vote_date = info_data.get('date')
            self.vote_options_count = {
                'attendance_count': info_data.get('attendance', 0),
                'agree_count': info_data.get('agree', 0),
                'disagree_count': info_data.get('disagree', 0),
                'abstain_count': info_data.get('abstain', 0),
                'novote_count': info_data.get('novote', 0),
            }
            
        return {
            'date': self.vote_date,
            'option_count': self.vote_options_count
        }
    
    def get_votes(self) -> list[dict[Hashable, Any]]:
        
        if self.votes_data is None:
            votes_data = []
            for page in tqdm(self.page_images, desc=self.get_vote_event_title()[:30] + "..."):
                # Crop to get only table
                table_img = get_table_image(page)
                row_images_data = get_rows_images_in_table(table_img)
                votes_data.extend(read_text_in_row_data(row_images_data))
            
            self.votes_data = votes_data
            self.check_extra_votes()
        
        return self.votes_data
    
    def get_votes_df(self) -> pd.DataFrame:
        if self.votes_data is None:
            self.get_votes()
            
        votes_df = pd.DataFrame(self.votes_data)
        votes_df.rename(columns=COLUMNS_INDEX_TH, inplace=True)
        return votes_df
    
    def check_extra_votes(self) -> None:
        
        votes_df = pd.DataFrame(self.votes_data)
        assert votes_df is not None
        
        # Check extra votes
        extra_row_images_data = get_extra_votes_images(self.page_images[-1])
        extra_votes_data = read_text_in_row_data(extra_row_images_data)
        
        for vote_data in extra_votes_data:
            voter_name = vote_data.get('voter_name', '')
            updated_vote_option = vote_data.get('vote_option', '')
            if voter_name in votes_df['voter_name'].unique():
                votes_df.loc[votes_df['voter_name'] == voter_name, 'vote_option'] = updated_vote_option
            else:
                votes_df = pd.concat(
                    [votes_df, pd.DataFrame([vote_data])],
                    ignore_index=True
                )
        
        self.votes_data = votes_df.to_dict('records')
        
    def to_dict(self) -> dict:
        vote_title = self.get_vote_event_title()
        vote_info = self.get_vote_info()
        
        votes_data = self.get_votes()
        
        return {
            "title": vote_title,
            "vote_info": vote_info,
            "votes_data": votes_data,
        }