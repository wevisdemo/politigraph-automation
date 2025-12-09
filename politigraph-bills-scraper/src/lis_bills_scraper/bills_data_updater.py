from typing import List, Dict, Any
import asyncio, os, re
import json
import pickle
import time

from poliquery import get_all_bills_info, get_representative_members_name, get_prime_minister_cabinet_index

from .bill_scraper import scrape_bill_list
from .bill_event_scraper import scrape_bill_events
from .instructor_manager import add_new_bill_instruction, add_new_events_instruction, add_update_events_instruction

from .lis_web_constants import BILL_EVENT_TYPENAME_INDEX

from poliquery import \
    create_bills_in_chunk, \
    create_bill_vote_event_in_chunk, \
    create_bill_merge_event_in_chunk, \
    create_bill_royal_assent_event_in_chunk, \
    create_bill_enact_event_in_chunk, \
    create_bill_reject_event_in_chunk
    
from poliquery import \
    update_bill_vote_events, \
    update_bill_royal_assent_events, \
    update_bill_enact_events, \
    update_bill_reject_events

def clean_up_files(
    exception: List[str]=[]
):
    filesname_to_delete = [
        'bill_list',
        'politigraph_bill_list',
        'merged_lis_id',
        'name_index',
        'prime_minister_index'
    ]
    
    for file_extension in ['.json', '.pkl']:
        
        # Construct file names list
        filenames = [
            n + file_extension for n in filesname_to_delete if n not in exception
        ]
        
        for filename in filenames:
            # Check if the file exists before attempting to delete it
            if os.path.exists(filename):
                os.remove(filename)
                print(f"File '{filename}' deleted successfully.")

def update_bills_data(
    parliament_terms: List[int]|None=None
):
    
    terms = parliament_terms
    # If parliament_term not provided get all terms from politigraph
    if not terms:
        terms = [25]
        
    for term in terms:
        
        _header_str = "".join("▒" for _ in range(25))
        print(_header_str , f"Term {term}", _header_str)
        
        # Scrape bill list
        _start_time = time.time()
        if os.path.exists('bill_list.pkl'):
            with open('bill_list.pkl', 'rb') as file:
                bills_list = pickle.load(file)
        else:
            bills_list = scrape_bill_list(parliament_term=term)
        _end_time = time.time()
        elapsed_time = _end_time - _start_time
        print(f"⏳ Scrape Bills completed in : {elapsed_time:.4f} seconds")
        
        # Save to file
        with open('bill_list.pkl', 'wb') as file:
            pickle.dump(bills_list, file)
            print(f"Scraped bills total : {len(bills_list)}")
            
        # Get bill list from politigraph
        politigraph_bill_list = asyncio.run(get_all_bills_info(parliament_terms=term))
        # Save to file
        with open('politigraph_bill_list.pkl', 'wb') as file:
            pickle.dump(politigraph_bill_list, file)
        
        # Load politician name index from politigraph & save to json
        politicians = get_representative_members_name(parliament_term=term)
        name_index = {}
        for person in politicians:
            name_index[person['name']] = person['id']
            if person['other_names']:
                for other_name in person['other_names']:
                    name_index[other_name['name']] = person['id']
        with open('name_index.pkl', 'wb') as file:
            pickle.dump(name_index, file)
            
        # Load prime minister index from politigraph & save to json
        prime_minister_index = asyncio.run(get_prime_minister_cabinet_index(None))
        with open('prime_minister_index.pkl', 'wb') as file:
            pickle.dump(prime_minister_index, file)
                    
        # Scrape billEvent
        _start_time = time.time()
        # scrape_bill_events()
        _end_time = time.time()
        elapsed_time = _end_time - _start_time
        print(f"⏳ Scrape events completed in : {elapsed_time:.4f} seconds")

        # Create bills
        print(f"⚙️ Creating bills...")
        _start_time = time.time()
        create_bills()
        _end_time = time.time()
        elapsed_time = _end_time - _start_time
        print(f"⏳ Create bills completed in : {elapsed_time:.4f} seconds")
        
        time.sleep(2)
        # Update politigraph bill list after create new bills
        with open('politigraph_bill_list.pkl', 'wb') as file:
            pickle.dump(
                asyncio.run(get_all_bills_info(parliament_terms=term)), 
                file
            )
            
        # Create billEvents
        print(f"⚙️ Creating billEvents...")
        _start_time = time.time()
        create_bill_events()
        _end_time = time.time()
        elapsed_time = _end_time - _start_time
        print(f"⏳ Create billEvents completed in : {elapsed_time:.4f} seconds")
        
        _start_time = time.time()
        update_bill_events()
        _end_time = time.time()
        elapsed_time = _end_time - _start_time
        print(f"⏳ Update bill events completed in : {elapsed_time:.4f} seconds")
        
        # Clean up file except some with reuseable values
        # - prime_minister_index
        clean_up_files(
            exception=[
                'bill_list',
                'prime_minister_index.pkl'
            ]
        )
        print(_header_str + "".join("▒" for _ in range(7)) + _header_str)
        time.sleep(30) # wait 30 sec, in case some operation still get processed in the server
    
            
def create_bills():
    
    # Load data from saved files
    with open('bill_list.pkl', 'rb') as file:
        bill_list = pickle.load(file)
    with open('politigraph_bill_list.pkl', 'rb') as file:
        politigraph_bill_list = pickle.load(file)
        
    # Reset create instructoin, if exist
    with open('create_bill_instruction.pkl', 'wb') as file:
        pickle.dump([], file)
        
    for idx, bill in enumerate(bill_list):
        
        # Check if bill already exist in politigraph
        matched_bill = next(
            (b for b in politigraph_bill_list\
                if b.get('lis_id') == bill['lis_id']\
                and b.get('acceptance_number') == bill['acceptance_number'])
            , None
        )
        if matched_bill: # if already exist, skip
            continue
        
        add_new_bill_instruction(bill=bill)
    
    # Create bills
    # Load create param instruction
    with open('create_bill_instruction.pkl', 'rb') as file:
        create_instructors = pickle.load(file)
        print(f"Total politigraph bills : {len(politigraph_bill_list)}")
        print(f"Total new bills : {len(create_instructors)}")
        
    # Create bills with poliquery
    asyncio.run(create_bills_in_chunk(params=create_instructors))
    
def create_bill_events():
    
    # Load data from saved files
    with open('bill_list.pkl', 'rb') as file:
        bill_list = pickle.load(file)
    with open('politigraph_bill_list.pkl', 'rb') as file:
        politigraph_bill_list = pickle.load(file)
        
    # Reset all create instructoins
    for typename in list(set(BILL_EVENT_TYPENAME_INDEX.values())):
        with open(f'create_bill_events_instruction_{typename}.pkl', 'wb') as file:
            # json.dump([], file, indent=4, ensure_ascii=False)
            pickle.dump([], file)
    with open(f'merged_lis_id.pkl', 'wb') as file:
            pickle.dump([], file)
        
    for idx, bill in enumerate(bill_list):
        
        # Check if bill already exist in politigraph
        matched_bill = next(
            (b for b in politigraph_bill_list\
                if b.get('lis_id') == bill['lis_id']\
                and b.get('acceptance_number') == bill['acceptance_number'])
            , None
        )
        
        # If no match, skip
        if not matched_bill:
            continue
        # Check status
        if matched_bill.get('status') != 'IN_PROGRESS': # bill is resolved
            continue
        
        # Get events
        politigraph_events = matched_bill.get('bill_events', [])
        
        # Add typename to event
        events = bill.get('bill_events', [])
        for event in events:
            event['__typename'] = BILL_EVENT_TYPENAME_INDEX.get(event.get('event_type'))
            event['classification'] = None
            if 'VOTE' in event['event_type']:
                event['classification'] = re.sub("VOTE_EVENT_", "", event['event_type'])
        bill['bill_events'] = events
        
        # Get new events
        all_events = bill.get('bill_events', [])
        new_events = [
            event for event in all_events
            if not any(
                event.get('__typename') == p_event.get('__typename') \
                    and event.get('classification', None) == p_event.get('classification', None)
                for p_event in politigraph_events
            )
        ]
        
        # Add ID to bill
        bill['id'] = matched_bill.get('id', '')
        
        add_new_events_instruction(
            bill=bill,
            events=new_events
        )
        
    # Create bill events
    # Load create param instruction
    for typename in list(set(BILL_EVENT_TYPENAME_INDEX.values())):
        with open(f'create_bill_events_instruction_{typename}.pkl', 'rb') as file:    
            create_instructors = pickle.load(file)
                
        create_event_handler = {
            'BillVoteEvent': create_bill_vote_event_in_chunk,
            'BillMergeEvent': create_bill_merge_event_in_chunk,
            'BillRoyalAssentEvent': create_bill_royal_assent_event_in_chunk,
            'BillEnactEvent': create_bill_enact_event_in_chunk,
            'BillRejectEvent': create_bill_reject_event_in_chunk,
        }.get(typename, None)
        if not create_event_handler:
            continue
        asyncio.run(create_event_handler(params=create_instructors))
        print(f"Total {typename} created : {len(create_instructors)}")
        
def update_bill_events():
    
    # Load data from saved files
    with open('bill_list.pkl', 'rb') as file:
        bill_list = pickle.load(file)
    with open('politigraph_bill_list.pkl', 'rb') as file:
        politigraph_bill_list = pickle.load(file)
        
    # Reset all update instructoins
    for typename in list(set(BILL_EVENT_TYPENAME_INDEX.values())):
        with open(f'update_bill_events_instruction_{typename}.pkl', 'wb') as file:
            pickle.dump([], file)
        
    for idx, bill in enumerate(bill_list):
        
        # Check if bill already exist in politigraph
        matched_bill = next(
            (b for b in politigraph_bill_list\
                if b.get('lis_id') == bill['lis_id']\
                and b.get('acceptance_number') == bill['acceptance_number'])
            , None
        )
        
        if not matched_bill:
            continue
        
        # Add ID to bill
        bill['id'] = matched_bill.get('id', '')
        
        # Get events
        politigraph_events = matched_bill.get('bill_events', [])
        
        # Add typename to event
        events = bill.get('bill_events', [])
        for event in events:
            event['__typename'] = BILL_EVENT_TYPENAME_INDEX.get(event.get('event_type'))
        bill['bill_events'] = events
        
        # Check event that need to get update
        event_to_update = []
        for event in events:
            matched_event: Dict[str, Any]|None = next(
                (e for e in politigraph_events\
                    if e.get('__typename') == event['__typename']\
                    and e.get('classification') == event.get('classification'))
                , None
            )
            if not matched_event:
                continue
            
            event_id = matched_event.get('id')
            
            # Check if this event has any change in data
            field_list = list(matched_event.keys())
            field_list = [
                e for e in field_list if e not in ['id', '__typename']
            ] # remove id & __typename from key to check
            
            # print(matched_event.get('__typename'), event_id, ">>>>>")
            for field in field_list:
                old_value = matched_event.get(field, None)
                new_value = event.get(field, None)
                
                if new_value and new_value != old_value:
                    event['id'] = event_id
                    event_to_update.append(event)
                    break # if at least one field is different, then add to update
                    
        add_update_events_instruction(
            bill=bill,
            events=event_to_update
        )
        
    # Update bill events
    # Load update param instruction
    for typename in list(set(BILL_EVENT_TYPENAME_INDEX.values())):
        with open(f'update_bill_events_instruction_{typename}.pkl', 'rb') as file:    
            update_instructors = pickle.load(file)
            
        print(f"Update {len(update_instructors)} {typename} ...")
                
        update_event_handler = {
            'BillVoteEvent': update_bill_vote_events,
            'BillMergeEvent': None,
            'BillRoyalAssentEvent': update_bill_royal_assent_events,
            'BillEnactEvent': update_bill_enact_events,
            'BillRejectEvent': update_bill_reject_events,
        }.get(typename, None)
        if not update_event_handler:
            continue
        asyncio.run(update_event_handler(params=update_instructors))