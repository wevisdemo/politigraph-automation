from typing import List, Dict, Any, Hashable
import re
import asyncio

import pandas as pd
from poliquery import get_all_bills_info, update_bill_info

from .bill_events_scraper import scrape_bill_events


event_handler_dispatcher = {
    'GENERAL_INFO': update_bill_info,
}

def update_event_in_bill(
    bill: Dict[str, Any],
    bill_events: List[Dict[str, Any]]
) -> None:
    
    print("Hello from update_event_in_bill")
    for event_info in bill_events:
        event_handler = event_handler_dispatcher.get(event_info['event_type'], None)
        if not event_handler:
            continue
        event_handler(
            bill_info=bill,
            event_info=event_info
        )
        
async def scrape_bill_events_data(parliament_terms:int) -> List[Dict[str, Any]]:
    
    bill_events_data = []
    
    lock = asyncio.Lock()
    
    # Get all bills info
    async with lock:
        bills_info = await get_all_bills_info(parliament_terms=parliament_terms)

    for bill in bills_info:
        # Get url to scrape billEvents
        url = bill['links'][0]['url']
        
        # Scrape bill events data
        bill_events = await scrape_bill_events(url)
        
        # Append to main list
        bill_events_data.append({
            'bill': bill,
            'bill_events': bill_events
        })
    
    return bill_events_data

def scrape_and_update_bill_events(
    parliament_term: int
) -> None:
    
    update_bill_events_info = asyncio.run(scrape_bill_events_data(parliament_terms=parliament_term))
    
    for update_info in update_bill_events_info:
        bill = update_info['bill']
        bill_events = update_info['bill_events']
        
        update_event_in_bill(
            bill=bill,
            bill_events=bill_events
        )
        
    