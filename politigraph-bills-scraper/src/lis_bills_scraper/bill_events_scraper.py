from typing import List, Dict, Any
import requests
import re

from bs4 import BeautifulSoup
from .event_scapers import event_scraper_dispatcher

async def scrape_bill_events(
    url: str
) -> List[Dict[str, Any]]:
    """_summary_

    Args:
        url (str): _description_

    Raises:
        ValueError: _description_

    Returns:
        List[Dict[str, Any]]|None: _description_
    """
    
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
    