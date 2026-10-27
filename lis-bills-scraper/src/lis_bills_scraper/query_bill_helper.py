from typing import Any
import time
import asyncio
from .bills import Bill
from .events import (
    BillRejectEvent
)

from .data_loader import (
    load_bill_data, 
    refresh_bill_data,
    load_parliament_info
)
from .param_helper import (
    generate_create_bill_param,
    generate_co_proposer_connect_param
)

from .query_event_helper import create_new_reject_event

from poliquery import (
    get_apollo_client, 
    create_bill, 
    update_bill,
)

from .utilities import get_status_from_raw

def find_matching_bill(bill: Bill, parliament_term: int) -> dict[str, Any] | None:
    
    bills_data = load_bill_data(parliament_term)
                
    # Check if bill exist
    matched_bill = next(
        (
            _bill for _bill in bills_data \
                if _bill.get('classification') == bill.classification \
                and _bill.get('acceptance_number') == bill.acceptance_number \
                and _bill.get('proposal_date') == bill.proposal_date \
        ),
        None
    )
    
    return matched_bill
        
def create_new_bill(bill: Bill) -> None:
    
    # Check if bill exist
    matched_bill = find_matching_bill(bill, bill.get_parliament_term())
    if matched_bill:
        bill.id = matched_bill.get('id')
        
        # Update status
        bill.status = matched_bill.get('status', 'IN_PROGRESS')
        return
    
    # Check for zombie bill
    parliament_info = load_parliament_info(bill.get_parliament_term())
    if parliament_info \
    and parliament_info.get('founding_date', "2000-01-01") > bill.proposal_date:
        # Handle zombie bill
        print("\n=+=+=+=+= zombie bill =+=+=+=+=")   
        print(f"Title : {bill.title}")
        
        # Add lis_id to old bill
        previous_parliament_term = bill.get_parliament_term() - 1
        matched_bill = find_matching_bill(bill, previous_parliament_term)
        if matched_bill:
            bill.id = matched_bill.get('id')
            print("=+=+=+=+= found match bill =+=+=+=+=")
            print(f"ID : {bill.id}")
            
            # Update status
            bill.status = matched_bill.get('status', 'IN_PROGRESS')
            print(f"Status : {bill.status}")
            
            if bill.lis_id in matched_bill['lis_ids']:
                return
            
            update_lis_param = {
                "where": {
                    "id": {
                        "eq": bill.id
                    }
                },
                "update": {
                    "lis_ids": {
                        "push": bill.lis_id
                    },
                    "links": [
                        {
                            "create": [
                            {
                                "node": {
                                    "note": "ระบบสารสนเทศด้านนิติบัญญัติ",
                                    "url": bill.url
                                }
                            }
                            ]
                        }
                    ],
                    "organizations": [ # Connect to current parliament
                        {
                            "connect": [
                                {
                                    "where": {
                                        "node": {
                                            "id": f"สภาผู้แทนราษฎร-{bill.get_parliament_term()}"
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
            asyncio.run(update_bill(client=get_apollo_client(), params=update_lis_param))
            print(f"added lis_id : {bill.lis_id} to bill")
        else:
            print(f"no matched bill in term : {previous_parliament_term}")
        return
            
    create_bill_param = generate_create_bill_param(bill)
    
    # Create bill & get id
    apollo_client = get_apollo_client()
    result = asyncio.run(create_bill(apollo_client, params=create_bill_param))
    created_bill = next(iter(result.get('createBills', {}).get('bills', [])), None)
    
    # Update bill ID
    bill.id = created_bill['id'] # type: ignore
    print("\n=+=+=+=+= created new bill =+=+=+=+=")
    print(f"ID : {bill.id}")
    print(f"Title : {bill.title}")
    print(f"proposer : {bill.proposer_name}")
    if bill.creator_type == "ASSEMBLY":
        print(f"cabinet : {bill.prime_minister_name}")
    
    # Add co-creators
    connect_co_creators_params = generate_co_proposer_connect_param(bill)
    if connect_co_creators_params:
        print("+ + + + + + + + + + +")
        for param in connect_co_creators_params:
            asyncio.run(update_bill(client=apollo_client, params=param))
            print(f"connected {len(param['update']['co_creators'][0]['connect'])} co-proposers ...")
    
    time.sleep(0.5)
    refresh_bill_data(parliament_term=bill.get_parliament_term())
    
def update_bill_status(bill: Bill, new_status: str) -> None:
    
    upadte_status_param = {
        "where": {
            "id": {
                "eq": bill.id
            }
        },
        "update": {
            "status": {
                "set": new_status
            }
        }
    }
    
    asyncio.run(update_bill(
        client=get_apollo_client(),
        params=upadte_status_param
    ))
    
def cleanup_bill(bill: Bill) -> None:
    
    # Check if raw status text match status
    status_from_raw = get_status_from_raw(bill.status_raw)
    status = bill.status
    
    if status != 'IN_PROGRESS':
        return
    
    def print_update(bill: Bill):
        # Initialize the attribute on the function if it doesn't exist yet
        if not hasattr(print_update, "has_run"):
            print_update.has_run = False
            
        if not print_update.has_run:
            print("\n=+=+=+=+= cleanup bill =+=+=+=+=")
            print(f"ID : {bill.id}")
            print(f"Title : {bill.title}")
            print("+ + + + + + + + + + +")
            print_update.has_run = True
    
    # If status does not match
    if status_from_raw != status:
        # Update status
        print_update(bill)
        print(f"update status {status} -> {status_from_raw}")
        update_bill_status(bill=bill, new_status=status_from_raw)
        bill.status = status_from_raw
        status = bill.status
        
        # Check if bill reject
        if status == 'REJECTED':
            # Check for reject event
            if not any(
                type(event) == 'BillRejectEvent' for event in bill.events
            ):
                # Add reject event
                create_new_reject_event(
                    bill=bill,
                    event=BillRejectEvent({
                        'reject_reason': bill.status_raw
                    })
                )
