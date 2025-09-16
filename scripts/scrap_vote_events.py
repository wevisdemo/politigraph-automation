# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "msbis-vote-events-scraper",
#     "thai_name_normalizer", "poliquery", "python-dotenv", "requests"
# ]
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# msbis-vote-events-scraper = { path = "../politigraph_vote_events_scraper", editable = true }
# thai_name_normalizer = { path = "../politigraph-name-normalizer", editable = true }
# ///
import os
import requests
from msbis_vote_events_scraper import scrap_msbis_vote_events
from poliquery import create_new_vote_event, get_latest_parliament_term, get_latest_msbis_id, create_vote_event


def download_pdf(url, filepath):
    """
    Download a PDF file from the given URL and save it to the specified filepath.
    """
    response = requests.get(url)
    if response.status_code == 200:
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath))
        # Save the PDF file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded PDF to {filepath}")

def main() -> None:
    
    print("Hello from scrap_vote_events.py!")
    
    # Get latest parliament number
    latest_parliament_term = get_latest_parliament_term()  
    
    # Get latest msbis_id from VoteEvents
    latest_msbis_id = get_latest_msbis_id()
    
    print(f"Latest Parliament Number: {latest_parliament_term}")
    print(f"Latest MSBIS ID: {latest_msbis_id}")
    
    vote_event_data = scrap_msbis_vote_events(
        parliament_num=latest_parliament_term, 
        latest_id=latest_msbis_id
    )
    vote_event_data = [
        event for event in vote_event_data if event['classification'] != 'ETC'
    ]
    # Convert date in data to string format
    for event in vote_event_data:
        event['start_date'] = event['vote_date'].strftime('%Y-%m-%d')
        
    ### Download pdf files & add VoteEvent to politigraph, then contruct data for OCR
    # Create directory for PDF files
    pdf_dir_pth = "vote_log_pdf"
    if not os.path.exists(pdf_dir_pth):
        os.makedirs(pdf_dir_pth)
    # Initialize OCR data list
    ocr_data = []
    
    msbis_ids = sorted([event['msbis_id'] for event in vote_event_data])
    print(f"MSBIS IDs: {msbis_ids}")
    
    for vote_event in vote_event_data:
        pdf_link = vote_event.get('pdf_url', None)
        include_senate = vote_event.get('include_senate', False)
        
        if pdf_link:
            pdf_filename = vote_event.get('pdf_file_name', pdf_link.split("/")[-1])
            try:
                # Download the PDF file
                pdf_filepath = os.path.join(pdf_dir_pth, pdf_filename)
                download_pdf(pdf_link, pdf_filepath)
                # Add new VoteEvent to politigraph
                print(vote_event)
                vote_event_id = create_new_vote_event(
                    parliament_term=latest_parliament_term,
                    vote_event_info=vote_event,
                    include_senate=include_senate
                )
                
                ocr_data.append({
                    'title': vote_event['title'],
                    'msbis_id': vote_event['msbis_id'],
                    'start_date': vote_event['start_date'],
                    'pdf_file_name': pdf_filename,
                    'pdf_url': pdf_link,
                    'file_path': pdf_filepath,
                    'vote_event_id': vote_event_id
                })
                print("Created VoteEvent with ID:", vote_event_id)
                
            except Exception as e:
                print(f"Error creating VoteEvent msbis_id {vote_event['msbis_id']}: {e}")
                continue
    
    import json
    with open("vote_events.json", "w", encoding="utf-8") as f:
        json.dump(ocr_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
