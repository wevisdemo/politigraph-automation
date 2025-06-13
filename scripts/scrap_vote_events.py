# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "msbis-vote-events-scraper",
#     "poliquery", "python-dotenv", "requests"
# ]
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# msbis-vote-events-scraper = { path = "../politigraph_vote_events_scraper", editable = true }
# ///
import os, io
import requests
from dotenv import load_dotenv
from msbis_vote_events_scraper import scrap_msbis_vote_events
from poliquery import get_apollo_client, get_latest_parliament_number, get_latest_msbis_id, create_vote_event


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
    
    load_dotenv()
    
    POLITIGRAPH_SUBSCRIBTION_ENDPOINT = os.getenv("POLITIGRAPH_SUBSCRIBTION_ENDPOINT")
    POLITIGRAPH_TOKEN = os.getenv("POLITIGRAPH_TOKEN")
    
    print("Hello from scrap_vote_events.py!")
    
    # Initialize Apollo Client
    apollo_client = get_apollo_client(
        POLITIGRAPH_SUBSCRIBTION_ENDPOINT,
        POLITIGRAPH_TOKEN
    )
    
    # Get latest parliament number
    latest_parliament_num = get_latest_parliament_number(apollo_client)  
    
    # Get latest msbis_id from VoteEvents
    latest_msbis_id = get_latest_msbis_id(apollo_client)
    
    print(f"Latest Parliament Number: {latest_parliament_num}")
    print(f"Latest MSBIS ID: {latest_msbis_id}")
    
    vote_event_data = scrap_msbis_vote_events(
        parliament_num=latest_parliament_num, 
        latest_id=latest_msbis_id
    )
    # Convert date in data to string format
    for event in vote_event_data:
        event['start_date'] = event['vote_date'].strftime('%Y-%m-%d')
        
    ### Download pdf files & add VoteEvent to politigraph, then contruct data for OCR
    # Initialize Apollo Client
    apollo_client = get_apollo_client(
        POLITIGRAPH_SUBSCRIBTION_ENDPOINT,
        POLITIGRAPH_TOKEN
    )
    # Create directory for PDF files
    pdf_dir_pth = "vote_log_pdf"
    if not os.path.exists(pdf_dir_pth):
        os.makedirs(pdf_dir_pth)
    # Initialize OCR data list
    ocr_data = []
    
    # TODO Remove this part
    # Skip the latest msbis_id
    msbis_ids = sorted([event['msbis_id'] for event in vote_event_data])
    print(f"MSBIS IDs: {msbis_ids}")
    latest_msbis_id = msbis_ids[-1]
    vote_event_data = [event for event in vote_event_data if event['msbis_id'] != latest_msbis_id]
    
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
                # vote_event_id = "000ZZZ"
                print(vote_event)
                vote_event_id = create_vote_event(
                    client=apollo_client, 
                    parliament_num=latest_parliament_num,
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
                
            except Exception as e:
                print(f"Error creating VoteEvent msbis_id {vote_event['msbis_id']}: {e}")
                continue
    
    import json
    with open("vote_events.json", "w", encoding="utf-8") as f:
        json.dump(ocr_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
