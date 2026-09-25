import os
import json
from pathlib import Path
import pandas as pd
from vote_doc_reader import get_vote_log_object
from vote_log_manager import clean_votes_df, add_votes, update_vote_counts
    
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# PDF from scraper
PDF_DIR = OUTPUT_DIR / "vote_log_pdf"

# CSV out
CSV_OUT_DIR = OUTPUT_DIR / "votes_csv"

def main() -> None:
    
    # Load vote event data
    with open(OUTPUT_DIR / "vote_events.json", "r", encoding="utf-8") as f:
        ocr_data = json.load(f)
        
    for vote_event in ocr_data:
            
        vote_event_id = vote_event.get("vote_event_id", None)
        if not vote_event_id:
            print("No vote_event_id found, skipping...")
            continue
        
        print(f"OCR votes for vote event ID : {vote_event_id}")
        pdf_file_path = vote_event.get("file_path", None)
        vote_log = get_vote_log_object(pdf_file_path)
        
        # Update info
        vote_log_info = vote_log.get_vote_info()
        update_vote_counts(
            vote_event_id=vote_event_id,
            vote_count_data=vote_log_info.get('option_count', {})
        )
        
        # Votes
        votes_df = vote_log.get_votes_df()
        
        # Clean votes df
        votes_df = clean_votes_df(votes_df)
        
        # Add votes
        add_votes(
            vote_event_id,
            votes_df
        )
        

if __name__ == "__main__":
    main()