from typing import List, Dict, Any, Hashable
import re
import asyncio

from poliquery import get_all_bills_info, update_bill_info, \
    update_bill_co_proposer, create_new_draft_vote_event, \
    create_new_royal_assent_event, create_new_enforce_event, \
    create_new_reject_event, create_new_merge_event

from .bill_events_scraper import scrape_bill_events


event_handler_dispatcher = {
    'GENERAL_INFO': update_bill_info,
    'CO_PROPOSER': update_bill_co_proposer,
    'VOTE_EVENT_MP_1': create_new_draft_vote_event,
    'VOTE_EVENT_MP_3': create_new_draft_vote_event,
    'VOTE_EVENT_SENATE_1': create_new_draft_vote_event,
    'VOTE_EVENT_SENATE_3': create_new_draft_vote_event,
    'ROYAL_ASSENT': create_new_royal_assent_event,
    'ENFORCE': create_new_enforce_event,
    'REJECT': create_new_reject_event,
    'MERGE': create_new_merge_event,
}

def update_event_in_bill(
    bill: Dict[str, Any],
    bill_events: List[Dict[str, Any]]
) -> None:
    
    print("Hello from update_event_in_bill")
    for event_info in bill_events:
        event_handler = event_handler_dispatcher.get(event_info.get('event_type', ""), None)
        if not event_handler:
            continue
        event_handler(
            bill_info=bill,
            event_info=event_info
        )
        
def is_bill_resolved(bill_status: str) -> bool:
    
    # Check reject bill
    if re.search('ตกไป', bill_status):
        return True
    
    # Check merge bill
    if re.search('ถูกรวมร่าง', bill_status):
        return True
    
    # Check enforce bill
    if re.search('ประกาศในราชกิจจานุเบกษา', bill_status):
        return True
    
    return False

async def scrape_bill_events_data(
    parliament_terms:int,
    ignore_bill_status:bool=False
) -> List[Dict[str, Any]]:
    
    bill_events_data = []
    
    lock = asyncio.Lock()
    
    # Get all bills info
    async with lock:
        bills_info = await get_all_bills_info(parliament_terms=parliament_terms)

    for bill in bills_info:
        
        # Check bill's status
        bill_status = bill.get('status', '')
        if not ignore_bill_status and is_bill_resolved(bill_status):
            print(f"\nbill status : {bill_status}\n")
            continue
        
        print("\n╔" + "".join('═' for _ in range(45)) + "╗")
        print(f"Start scraping bill : {bill['id']}")
        # Get url to scrape billEvents
        url = bill['links'][0]['url']
        
        # Scrape bill events data
        bill_events = await scrape_bill_events(url)
        
        # Append to main list
        bill_events_data.append({
            'bill': bill,
            'bill_events': bill_events
        })
        print("╚" + "".join('═' for _ in range(45)) + "╝\n")
    
    return bill_events_data

def scrape_and_update_bill_events(
    parliament_term: int,
    ignore_bill_status:bool=False
) -> None:
    
    update_bill_events_info = asyncio.run(scrape_bill_events_data(
        parliament_terms=parliament_term, 
        ignore_bill_status=ignore_bill_status
    ))
    
    for update_info in update_bill_events_info:
        bill = update_info['bill']
        bill_events = update_info['bill_events']
        
        update_event_in_bill(
            bill=bill,
            bill_events=bill_events
        )
        
    