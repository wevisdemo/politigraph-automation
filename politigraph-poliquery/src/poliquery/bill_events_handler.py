from typing import List, Dict, Any, Hashable
import asyncio
from gql import Client

from .apollo_connector import get_apollo_client
from .query_helper.royal_assent_event import create_royal_assent_event, update_royal_assent_event
from .query_helper.enact_event import create_enact_event, update_enact_event
from .query_helper.reject_event import create_reject_event, update_reject_event
from .query_helper.bill_vote_event import create_bill_vote_event, update_bill_vote_event
from .query_helper.bills import update_bill
from .query_helper.merge_event import get_merge_events, create_merge_event


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

################################ GET #################################
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV#

async def get_bill_merge_events(id: str|None):
    # Initiate client
    apollo_client = get_apollo_client()
    where_param = {}
    if id:
        where_param = {
            'where': {
                'id_EQ': id
            }
        }
    return await get_merge_events(
        client=apollo_client,
        fields=[
            'id',
            'total_merged_bills',
            'main_bill_id',
            'bills { \n\tid\n\ttitle\n\tcreators {\n\t... on Person {\n\t\tid\n\t\tprefix\n\t\tname\n\t}\n\t... on Organization {\n\t\tid\n\t\tname\n\t}}\n\tlinks { \n\t\tnote\n\t\turl\n\t}\n}',
        ],
        params=where_param
    )
    

############################### CREATE ###############################
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV#

async def create_bill_vote_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    for param_chunk in chunker(params, batch_size):
        await create_bill_vote_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
        await asyncio.sleep(2)
    
    return

async def create_bill_merge_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    for param_chunk in chunker(params, batch_size):
        await create_merge_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
        await asyncio.sleep(2)
    
    return

async def create_bill_royal_assent_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    for param_chunk in chunker(params, batch_size):
        await create_royal_assent_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
        await asyncio.sleep(2)
    
    return

async def create_bill_enact_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    for param_chunk in chunker(params, batch_size):
        await create_enact_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
        
    # Curate bill ID to update status to Rejected
    bill_ids = [
        p['bills']['connect'][0]['where']['node']['id_EQ'] for p in params
    ]
    # Update these bills status to REJECT
    for bill_id in bill_ids:
        await update_bill(
            client=apollo_client,
            params={
                "where": {
                    "id_EQ": bill_id
                },
                "update": {
                    "status_SET": "ENACTED"
                }
            }
        )
        await asyncio.sleep(2)
    
    return

async def create_bill_reject_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    # Create Reject event
    for param_chunk in chunker(params, batch_size):
        await create_reject_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
        
    # Curate bill ID to update status to Rejected
    bill_ids = [
        p['bills']['connect'][0]['where']['node']['id_EQ'] for p in params
    ]
    # Update these bills status to REJECT
    for bill_id in bill_ids:
        await update_bill(
            client=apollo_client,
            params={
                "where": {
                    "id_EQ": bill_id
                },
                "update": {
                    "status_SET": "REJECTED"
                }
            }
        )
        await asyncio.sleep(2)
    
    return

############################### UPDATE ###############################
#VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV#

async def update_bill_vote_events(
    params: List[Dict[str, Any]]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    for param in params:
        await update_bill_vote_event(
            client=apollo_client,
            params=param
        )
        await asyncio.sleep(2)
        
    return

async def update_bill_royal_assent_events(
    params: List[Dict[str, Any]]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    for param in params:
        await update_royal_assent_event(
            client=apollo_client,
            params=param
        )
        await asyncio.sleep(2)
        
    return

async def update_bill_enact_events(
    params: List[Dict[str, Any]]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    for param in params:
        await update_enact_event(
            client=apollo_client,
            params=param
        )
        await asyncio.sleep(2)
        
    return

async def update_bill_reject_events(
    params: List[Dict[str, Any]]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    for param in params:
        await update_reject_event(
            client=apollo_client,
            params=param
        )
        await asyncio.sleep(2)
        
    return