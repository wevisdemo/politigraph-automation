from typing import List, Dict, Any

import pandas as pd
import easyocr

from politigraph_votes_extractor import extract_doc_data, extract_votelog, clean_votelog_df, extract_extra_votes, clean_extra_votes_df
from .validate_votes import validate_votes
from .data_helper import update_extra_votes

from poliquery import get_votes_from_vote_event, get_validation_data, update_vote_event_validation_data, add_votes_to_vote_event, replace_votes_in_vote_event

def update_validation_data(
    pdf_file_path: str,
    vote_event_id: str,
    reader:easyocr.Reader|None=None
):
    # Extract doc data
    doc_data = extract_doc_data(pdf_file_path, reader)
    
    validation_data = doc_data.get('validation_data', {})
    
    update_vote_event_validation_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=None
    )

    return validation_data

def validate_votes_doc(
    pdf_file_path: str,
    vote_event_id: str,
    reader:easyocr.Reader|None=None
) -> pd.DataFrame:
    # Extract doc data
    doc_data = extract_doc_data(pdf_file_path, reader)
    votes_df = extract_votelog(pdf_file_path, reader)
    
    validation_data = doc_data.get('validation_data', {})
    
    publish_status = "PUBLISHED" if validate_votes(
        votes_df, validation_data
    ) else "ERROR"
    
    update_vote_event_validation_data(
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
    
    validation_data = get_validation_data(vote_event_id)
    publish_status = "PUBLISHED" if validate_votes(
        votes_df=votes_df, 
        validate_data=validation_data
    ) else "ERROR"
    
    # Check if publish status remain the same
    if validation_data['publish_status'] == publish_status:
        print(f"Publish status remain unchanged: {publish_status}")
        return votes_df
        
    print(f"Validate: {publish_status}")
    
    update_vote_event_validation_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )

    return votes_df
    

def ocr_votes_doc(
    pdf_file_path: str,
    reader: easyocr.Reader
) -> pd.DataFrame:
    """
    OCR pdf document and return a result as pandas dataframe

    Args:
        pdf_file_path: str
            path to pdf file
        reader: easyocr.Reader
            easyOCR reader for text recognition

    Returns:
        OCR result
    """
    
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
    reader:easyocr.Reader
) -> None:
    """
    OCR pdf document and add new votes to the voteEvent

    Args:
        pdf_file_path: str
            path to pdf file
        vote_event_id: str
            ID of the voteEvent
        reader: easyocr.Reader
            easyOCR reader for text recognition
    """
    
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
    
    vote_logs = votes_df.to_dict('records')
    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        vote_logs=vote_logs, # type: ignore
    )
    
    update_vote_event_validation_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )
    
def batch_ocr_and_add_votes(
    data_dict: List[Dict[str, Any]],
    pdf_file_dir: str="pdf_files",
    reader:easyocr.Reader|None=None
) -> None:
    """
    OCR multiple pdf documents and add new votes to each voteEvent

    Args:
        data_dict: List[Dict[str, Any]]
            List of data dict contain OCR information
        pdf_file_dir: str
            Path to directory contains all of the pdf documents
        reader: easyocr.Reader
            easyOCR reader for text recognition
    """
    
    if not reader:
        return
    
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
    reader:easyocr.Reader
) -> pd.DataFrame:
    """
    OCR pdf document and update new votes to replace old votes in voteEvent

    Args:
        pdf_file_path: str
            path to pdf file
        vote_event_id: str
            ID of the voteEvent
        reader: easyocr.Reader
            easyOCR reader for text recognition
    Returns:
        OCR result
    """
    
    # Extract votes data
    votes_df = extract_votelog(pdf_file_path, reader)
    # Clean votes df
    votes_df = clean_votelog_df(votes_df)
    
    doc_data = extract_doc_data(pdf_file_path, reader)
    if doc_data['had_extra_votes']: # have extrac votes
        extra_votes_df = extract_extra_votes(pdf_file_path, reader)
        extra_votes_df = clean_extra_votes_df(extra_votes_df)
        votes_df = update_extra_votes(votes_df,extra_votes_df)
    
    vote_logs = votes_df.to_dict('records')
    replace_votes_in_vote_event(
        vote_event_id=vote_event_id,
        vote_logs=vote_logs, # type: ignore
    )
    
    validation_data = doc_data.get('validation_data', {})
    publish_status = "PUBLISHED" if validate_votes(
        votes_df, validation_data
    ) else "ERROR"
    
    update_vote_event_validation_data(
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )
    
    return votes_df
    
def add_votes_with_csv(
    vote_event_id: str,
    csv_file_path: str,
) -> None:
    import pandas as pd
    votes_df = pd.read_csv(csv_file_path)
    votes_df.fillna("", inplace=True)

    vote_logs = votes_df.to_dict('records')
    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        vote_logs=vote_logs, # type: ignore
    )
    