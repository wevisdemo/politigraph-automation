from typing import List, Dict, Any
import os, requests
import json
import pickle
from dotenv import load_dotenv
from tqdm.auto import tqdm

from bs4 import BeautifulSoup

from .event_scapers import event_scraper_dispatcher

def scrape_event(bill: Dict[str, Any]) -> List[Dict[str, Any]]:
    
    # Get url
    url = bill.get('url', None)
    if not url:
        return []
    
    # GET bills info page
    response = requests.get(url)
    
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    # Find h3 heading
    heading_element = soup.find('h3', {'class': 'heading'})
    if not heading_element:
        raise ValueError("No Bill heading!!")
    if not heading_element.parent:
        return []
    
    # Loop through to get all event's sections
    events_element: List[tuple] = []
    elements = heading_element.parent.find_all(recursive=False)
    for header, section in zip(elements, elements[1:]):
        if header.name == 'nav':  # type: ignore
            events_element.append(
                (header, section)
            )
            
    # Get data from each event
    events_data = []
    for event_index, (header_element, body_element) in enumerate(events_element):
        event_title = header_element.get_text(strip=True)
        
        event_handler = event_scraper_dispatcher.get(event_title, None)
        if not event_handler:
            continue
        curr_event_data = event_handler(body_element)
        
        # Add index to event's data
        curr_event_data['event_index'] = event_index
        
        # Append data to main list
        events_data.append(curr_event_data)
    
    return events_data

def scrape_bill_events():
    """Scrape bill event from every event and save to file

    Raises:
        FileNotFoundError: bill_list.pkl not found: possibly due to failed scrape
        FileNotFoundError: politigraph_bill_list.pkl not found: possibly due to failed connection with politigraph
    """
    
    # Check if bill_list.pkl exist
    if not os.path.exists('bill_list.pkl'):
        raise FileNotFoundError(
            "bill_list.pkl not found: possibly due to failed scrape"
        )
    # Check if politigraph_bill_list.pkl exist
    if not os.path.exists('politigraph_bill_list.pkl'):
        raise FileNotFoundError(
            "politigraph_bill_list.pkl not found: possibly due to failed connection with politigraph"
        )
    
    # Load data from saved files
    with open('bill_list.pkl', 'rb') as file:
        bill_list = pickle.load(file)
    with open('politigraph_bill_list.pkl', 'rb') as file:
        politigraph_bill_list = pickle.load(file)
        
    # Load env to check scrape mode
    load_dotenv()
    SCAPE_MODE = os.getenv('SCRAPE_MODE', None)
        
    for idx, bill in tqdm(enumerate(bill_list), disable=None):
        
        # Check status of bill from politigraph bill
        # If already resolved, then skip
        matched_bill = next(
            (b for b in politigraph_bill_list\
                if b.get('lis_id') == bill['lis_id']\
                and b.get('acceptance_number') == bill['acceptance_number'])
            , None
        )
        
        # If SCAPE_MODE is `ALL` then do not skip any bill whatsoever
        if matched_bill \
            and SCAPE_MODE != 'ALL' \
            and matched_bill.get('status', '') != 'IN_PROGRESS': # already resolved
            # print(f"Bill resolved with status : {matched_bill.get('status')}")
            continue
        
        # Scrape event
        events_data = scrape_event(bill)
        
        # Add to bill data
        bill['bill_events'] = events_data
        
    # Save to file
    with open('bill_list.pkl', 'wb') as file:
        pickle.dump(bill_list, file)