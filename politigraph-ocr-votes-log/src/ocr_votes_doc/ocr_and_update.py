from typing import List, Dict

import pandas as pd
import easyocr

from politigraph_votes_extractor import extract_doc_data, extract_votelog, clean_votelog_df, extract_extra_votes, clean_extra_votes_df
from .poliquery_helper import *
from .validate_votes import validate_votes

def update_validation_data(
    pdf_file_path: str,
    vote_event_id: str,
    reader:easyocr.Reader=None
):
    # Extract doc data
    doc_data = extract_doc_data(pdf_file_path, reader)
    
    validation_data = doc_data.get('validation_data', {})
    
    update_validate_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=None
    )

    return validation_data

def validate_votes_doc(
    pdf_file_path: str,
    vote_event_id: str,
    reader:easyocr.Reader=None
):
    # Extract doc data
    doc_data = extract_doc_data(pdf_file_path, reader)
    votes_df = extract_votelog(pdf_file_path, reader)
    
    validation_data = doc_data.get('validation_data', {})
    
    publish_status = "PUBLISHED" if validate_votes(
        votes_df, validation_data
    ) else "ERROR"
    
    update_validate_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )

    return votes_df

def re_validate_vote_event(
    vote_event_id: str,
):
    votes_data = get_votes_from_vote_event(vote_event_id)
    votes_df = pd.DataFrame(votes_data)
    
    # Rename columns
    ['id', 'vote_order', 'badge_number', 'voter_name', 'voter_party', 'option']
    votes_df.rename(
        columns={
            'id': 'id', 
            'vote_order': 'ลําดับที่', 
            'badge_number': 'เลขที่บัตร', 
            'voter_name': 'ชื่อ - สกุล', 
            'voter_party': 'ชื่อสังกัด', 
            'option': 'ผลการลงคะแนน'
        },
        inplace=True
    )
    
    validation_data = get_validation_data_from_vote_event(vote_event_id)
    
    publish_status = "PUBLISHED" if validate_votes(
        votes_df, validation_data
    ) else "ERROR"
    
    # Check if publish status remain the same
    if validation_data['publish_status'] == publish_status:
        print(f"Publish status remain unchanged: {publish_status}")
        return votes_df
        
    print(f"Validate: {publish_status}")
    
    update_validate_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )

    return votes_df
    

def ocr_votes_doc(
    pdf_file_path: str,
    reader:easyocr.Reader=None
) -> pd.DataFrame:
    # OCR
    votes_df = extract_votelog(pdf_file_path, reader)
    # Clean votes df
    votes_df = clean_votelog_df(votes_df)
    doc_data = extract_doc_data(pdf_file_path, reader) # TODO remove
    
    if doc_data['had_extra_votes']: # have extrac votes
        extra_votes_df = extract_extra_votes(pdf_file_path, reader)
        extra_votes_df = clean_extra_votes_df(extra_votes_df)
        votes_df = update_extra_votes(votes_df,extra_votes_df)
    
    return votes_df

def ocr_and_add_votes(
    pdf_file_path: str,
    vote_event_id: str,
    reader:easyocr.Reader=None
) -> None:
    # Extract votes data
    doc_data = extract_doc_data(pdf_file_path, reader)
    votes_df = extract_votelog(pdf_file_path, reader)
    # Clean votes df
    votes_df = clean_votelog_df(votes_df)
    
    if doc_data['had_extra_votes']: # have extrac votes
        extra_votes_df = extract_extra_votes(pdf_file_path, reader)
        extra_votes_df = clean_extra_votes_df(extra_votes_df)
        votes_df = update_extra_votes(votes_df,extra_votes_df)
    
    validation_data = doc_data.get('validation_data', {})
    
    publish_status = "PUBLISHED" if validate_votes(
        votes_df, validation_data
    ) else "ERROR"
    
    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        votes_df=votes_df,
    )
    
    update_validate_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )
    
def batch_ocr_and_add_votes(
    data_dict: list,
    pdf_file_dir: str="pdf_files",
    reader:easyocr.Reader=None
):
    
    for file_info in data_dict:
        filename = file_info.get("file_name", "")
        vote_event_id = file_info.get("vote_event_id", "")
        
        if not filename.endswith(".pdf"):
            continue
        
        import os
        pdf_file_pth = os.path.join(pdf_file_dir, filename)
        ocr_and_add_votes(
            pdf_file_path=pdf_file_pth,
            vote_event_id=vote_event_id,
            reader=reader
        )
        
def ocr_and_update_votes(
    pdf_file_path: str,
    vote_event_id: str,
    reader:easyocr.Reader=None
):
    # Extract votes data
    votes_df = extract_votelog(pdf_file_path, reader)
    # Clean votes df
    votes_df = clean_votelog_df(votes_df)
    
    doc_data = extract_doc_data(pdf_file_path, reader)
    if doc_data['had_extra_votes']: # have extrac votes
        extra_votes_df = extract_extra_votes(pdf_file_path, reader)
        extra_votes_df = clean_extra_votes_df(extra_votes_df)
        votes_df = update_extra_votes(votes_df,extra_votes_df)
    
    update_votes_in_vote_event(
        vote_event_id=vote_event_id,
        votes_df=votes_df,
        time_delay=0.2
    )
    
    validation_data = doc_data.get('validation_data', {})
    publish_status = "PUBLISHED" if validate_votes(
        votes_df, validation_data
    ) else "ERROR"
    
    update_validate_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )
    
    # re_validate_vote_event(vote_event_id)
    
    return votes_df
    
def add_votes_with_csv(
    vote_event_id: str,
    csv_file_path: str,
):
    import pandas as pd
    votes_df = pd.read_csv(csv_file_path)
    votes_df.fillna("", inplace=True)

    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        votes_df=votes_df,
    )
    
def update_extra_votes(
    votes_df: pd.DataFrame,
    extra_votes_df: pd.DataFrame,
    vote_options:list=["เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"],
    name_colum:str='ชื่อ - สกุล',
    vote_option_column:str='ผลการลงคะแนน'
) -> pd.DataFrame:
    
    df = votes_df.copy()
    
    # Filter out invalid vote options
    extra_votes_df = extra_votes_df.loc[
        extra_votes_df[vote_option_column].isin(vote_options)
    ]
    
    name_option_dict = extra_votes_df.set_index(name_colum)[vote_option_column].to_dict()
    for name, option in name_option_dict.items():
        df.loc[df[name_colum] == name, vote_option_column] = option
    
    return df
    