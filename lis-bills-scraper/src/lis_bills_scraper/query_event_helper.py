import asyncio
from .bills import Bill
from .events import (
    BillVoteEvent,
    BillMergeEvent,
    BillRoyalAssentEvent,
    BillEnactEvent,
    BillRejectEvent
)
from .data_loader import (
    load_bill_data, 
    refresh_bill_data
)
from .param_helper import (
    generate_create_bill_param,
    generate_co_proposer_connect_param
)

from poliquery import (
    get_apollo_client, 
    create_bill_vote_event,
    create_merge_event,
    create_royal_assent_event,
    create_enact_event,
    create_reject_event
)
from .msbis_scraper import get_msbis_id


def update_bill_events(bill: Bill) -> None:
    
    # Load bill events from politigraph
    bills_data = load_bill_data(bill.get_parliament_term())
    
    # Get bill data
    matched_bill = next(
        (
            _bill for _bill in bills_data \
                if _bill.get('classification') == bill.classification \
                and _bill.get('acceptance_number') == bill.acceptance_number \
                and _bill.get('proposal_date') == bill.proposal_date \
        ),
        None
    )
    if not matched_bill: # no bill
        return
    
    if bill.status != 'IN_PROGRESS':
        return
    
    def print_update(bill: Bill):
        # Initialize the attribute on the function if it doesn't exist yet
        if not hasattr(print_update, "has_run"):
            print_update.has_run = False
            
        if not print_update.has_run:
            print("\n=+=+=+=+= update events in bill =+=+=+=+=")
            print(f"ID : {bill.id}")
            print(f"Title : {bill.title}")
            print("+ + + + + + + + + + +")
            print_update.has_run = True
    
    existed_events = matched_bill.get('events', [])
    
    # Scraped bill events
    bill_events = bill.events
    for event in bill_events:
        if any(
            ev['__typename'] == str(type(event))
            and ev.get('classification') == event.classification
                for ev in existed_events
        ):  
            # TODO: update bill event instead
            continue
            
        dispatcher = BILL_EVENTS_CREATE_DISPATCHER.get(str(type(event)))
        if dispatcher is not None:
            print_update(bill)
            dispatcher(bill, event)
    refresh_bill_data(bill.get_parliament_term())
            
def create_new_vote_event(bill: Bill, event: BillVoteEvent) -> None:
    
    # Construct session identifier
    if any([event.session_year, event.session_number, event.session_type]):
        session_identifier = "การประชุม"
        session_identifier += f" ปีที่ {event.session_year}" if event.session_year else ""
        session_identifier += f" {event.session_type}" if event.session_type else ""
        session_identifier += f" ครั้งที่ {event.session_number}" if event.session_number else ""
        msbis_id = get_msbis_id(
            term=str(bill.get_parliament_term()),
            issue_year=event.session_year,
            session=event.session_type,
            issue_number=event.session_number,
        )
    else:
        session_identifier = None
        msbis_id = None
        
    param = {
        "title": bill.title,
        "classification": event.classification,
        "agree_count": event.agree_count,
        "disagree_count": event.disagree_count,
        "abstain_count": event.abstain_count,
        "novote_count": event.novote_count,
        "result": event.result,
        "session_identifier": session_identifier,
        "msbis_id": msbis_id,
        "start_date": event.date,
        "end_date": event.date,
        "bills": {
            "connect": [
                {
                    "where": {
                        "node": {
                            "id": {
                                "eq": bill.id
                            }
                        }
                    }
                }
            ]
        },
        "publish_status": "PUBLISHED"
    }
    
    # Create new BillVoteEvent
    create_bill_vote_event_param = {
        "input": [
            param
        ]
    }
    result = asyncio.run(create_bill_vote_event(
        client=get_apollo_client(),
        params=create_bill_vote_event_param
    ))
    print(f"created new BillVoteEvent {event.classification}")
    print(f"ID : {result['createBillVoteEvents']['billVoteEvents'][0]['id']}")
    print("+ + + + +")
        
def create_new_merge_event(bill: Bill, event: BillMergeEvent) -> None:
    
    connect_params = []
    for _bill in event.merged_bills:
        lis_id = _bill.get('lis_id')
        connect_params.append({
            "where": {
                "node": {
                    "lis_id": {
                        "eq": int(lis_id) if lis_id else None
                        # "contains": lis_id # TODO: update to this when change schema
                    }
                }
            }
        })
    # Add current bill to connect
    connect_params.append({
        "where": {
            "node": {
                "lis_id": {
                    "eq": int(bill.lis_id) if bill.lis_id else None
                    # "contains": lis_id # TODO: update to this when change schema
                }
            }
        }
    })
    
        
    param = {
        "total_merged_bills": event.total_merged_bills,
        "bills": {
            "connect": connect_params
        },
        "publish_status": "PUBLISHED"
    }
    
    # Create new BillVoteEvent
    create_bill_merge_event_param = {
        "input": [
            param
        ]
    }
    
    result = asyncio.run(create_merge_event(
        client=get_apollo_client(),
        params=create_bill_merge_event_param
    ))
    print(f"created new {type(event)} ...")
    print(f"ID : {result['createBillMergeEvents']['billMergeEvents'][0]['id']}")
    refresh_bill_data(bill.get_parliament_term()) # refresh to upadate bill events
    print("+ + + + +")
    
def create_new_royal_assent_event(bill: Bill, event: BillRoyalAssentEvent) -> None:
    
    param = {
      "result": event.result,
        "bills": {
            "connect": [
                {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill.id
                        }
                    }
                }
                }
            ]
        },
        "publish_status": "PUBLISHED"
    }
    
    # Create new BillRoyalAssentEvent
    create_bill_royal_assent_event_param = {
        "input": [
            param
        ]
    }
    
    result = asyncio.run(create_royal_assent_event(
        client=get_apollo_client(),
        params=create_bill_royal_assent_event_param
    ))
    print(f"created new {type(event)} ...")
    print(f"ID : {result['createBillRoyalAssentEvents']['billRoyalAssentEvents'][0]['id']}")
    print("+ + + + +")
    
def create_new_enact_event(bill: Bill, event: BillEnactEvent) -> None:
    
    param = {
        "title": event.title,
        "start_date": event.date,
        "end_date": event.date,
        "bills": {
            "connect": [
                {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill.id
                        }
                    }
                }
                }
            ]
        },
        "links": {
            "create": [
                {
                    "node": {
                        "note": "ราชกิจจานุเบกษา",
                        "url": event.announcement_report_link
                    }
                }
            ]
        },
        "publish_status": "PUBLISHED"
    }
    
    # Create new BillEnactEvent
    create_bill_enact_event_param = {
        "input": [
            param
        ]
    }
    
    result = asyncio.run(create_enact_event(
        client=get_apollo_client(),
        params=create_bill_enact_event_param
    ))
    print(f"created new {type(event)} ...")
    print(f"ID : {result['createBillEnactEvents']['billEnactEvents'][0]['id']}")
    print("+ + + + +")

def create_new_reject_event(bill: Bill, event: BillRejectEvent) -> None:
    
    param = {
        "reject_reason": event.reject_reason,
        "bills": {
            "connect": [
                {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill.id
                        }
                    }
                }
                }
            ]
        },
        "publish_status": "PUBLISHED"
    }
    
    # Create new BillRoyalAssentEvent
    create_bill_reject_event_param = {
        "input": [
            param
        ]
    }
    
    result = asyncio.run(create_reject_event(
        client=get_apollo_client(),
        params=create_bill_reject_event_param
    ))
    print(f"created new {type(event)} ...")
    print(f"ID : {result['createBillRejectEvents']['billRejectEvents'][0]['id']}")
    print("+ + + + +")

BILL_EVENTS_CREATE_DISPATCHER = {
    'BillVoteEvent': create_new_vote_event,
    'BillMergeEvent': create_new_merge_event,
    'BillRoyalAssentEvent': create_new_royal_assent_event,
    'BillEnactEvent': create_new_enact_event,
    'BillRejectEvent': create_new_reject_event,
}
    