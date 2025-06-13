# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "pandas", "easyocr",
#     "ocr_votes_doc",
#     "poliquery",
#     "politigraph_votes_extractor",
# ]
#
# [tool.uv.sources]
# ocr_votes_doc = { path = "../politigraph-ocr-votes-log", editable = true }
# poliquery = { path = "../politigraph-poliquery", editable = true }
# politigraph_votes_extractor = { path = "../politigraph-ocr-votes-log/politigraph-votes-log-extractor", editable = true }
# ///
import os
import easyocr

import pandas as pd

from ocr_votes_doc import ocr_and_add_votes, ocr_votes_doc

def main() -> None:
    print("Hello from ocr_and_and_votes.py!")
    
    # Initialize the OCR reader
    print("Initializing OCR reader...")
    ocr_model_dir = "models"
    assert os.path.exists(ocr_model_dir), "Please add the OCR model directory."
    reader = easyocr.Reader(['th'],
                recog_network='thai-vl',
                user_network_directory=ocr_model_dir,
                model_storage_directory=ocr_model_dir,
                detector=False,
                gpu=False,
                verbose=False)
    assert reader is not None, "Failed to initialize OCR reader."
    print("OCR reader initialized.")
    
    # Read OCR data
    import json
    with open("vote_events.json", "r", encoding="utf-8") as f:
        ocr_data = json.load(f)
        
    for vote_event in ocr_data:
        
        vote_event_id = vote_event.get("vote_event_id", None)
        if not vote_event_id:
            print("No vote_event_id found, skipping...")
            continue
        
        print("OCR votes for vote event ID:")

        ocr_and_add_votes(
            pdf_file_path=vote_event["file_path"],
            vote_event_id=vote_event_id,
            reader=reader,
        )
        print()

if __name__ == "__main__":
    main()
