from typing import List, Dict, Any
import time
import asyncio

from .appoint_committee_event_detector import get_appoint_committee_event_doc
from poliquery import get_bill_merge_events, update_main_bill_in_merge_events

def detect_main_bill(bill_list:List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    
    # Scrape each bill
    appoint_url_list = [] # contain doc url from appoint committee event
    result_url_list = [] # contain doc url from result committee event
    for bill in bill_list:
        lis_url = next(iter(
            [l for l in bill.get('links', []) if l.get('note') == 'ระบบสารสนเทศด้านนิติบัญญัติ']
        ), {}).get('url')
        
        if not lis_url:
            raise ValueError(f"No link for bill : {bill.get('id')}")
        
        appoint_comm_url, result_comm_url = get_appoint_committee_event_doc(lis_url)
            
        appoint_url_list.append({
            'id': bill.get('id'),
            'title': bill.get('title'),
            'proposer': next(iter(bill.get('creators', [])), None),
            'is_main_bill': True if appoint_comm_url else False,
            'doc_url': appoint_comm_url,
        })
        result_url_list.append({
            'id': bill.get('id'),
            'title': bill.get('title'),
            'proposer': next(iter(bill.get('creators', [])), None),
            'is_main_bill': True if result_comm_url else False,
            'doc_url': result_comm_url,
        })
        
    # Return the one with only one doc, if exist
    for lst in (appoint_url_list, result_url_list):
        if sum(1 for u in lst if u.get('is_main_bill')) == 1:
            return lst

    return max(
        appoint_url_list, 
        result_url_list, 
        key=lambda l: sum(1 for d in l if d.get('doc_url') is not None)
    )

def check_and_update_merge_bills(merge_event_id: str|None=None) -> List[Dict[str, Any]]:
    
    # Query merge event
    merge_events = asyncio.run(get_bill_merge_events(merge_event_id))
    
    failed_events = []
    
    # Update each merge events
    for merge_event in merge_events:
        # Check main bill
        if merge_event.get('main_bill_id'): # already got main bill
            continue
        
        # Get all bills
        bill_list = merge_event.get('bills', [])
        
        # Detect main bill
        print(f"Total bill in merge : {merge_event.get('total_merged_bills')}")
        checked_bills = detect_main_bill(bill_list)

        # Filter only main_bills
        main_bills = [
            bill for bill in checked_bills if bill.get('is_main_bill')
        ]
        
        # Check cases
        if len(main_bills) == 1: # found exactly 1 main bill -> Update
            # Update main bill
            print("UPDATE MAIN BILL...")
            asyncio.run(update_main_bill_in_merge_events(
                merge_event_id=merge_event.get('id'),
                main_bill_id=main_bills[0].get('id')
            ))
            time.sleep(1)
            print()
            continue
        elif len(main_bills) > 1: # found more than 1
            failed_events.append({
                'id': merge_event.get('id'),
                'total_merged_bills': merge_event.get('total_merged_bills'),
                'doc_url': main_bills[0].get('doc_url'),
                'checked_bills': checked_bills
            })
        
        # No main bill found -> ignore
        print()
    
    return failed_events
        