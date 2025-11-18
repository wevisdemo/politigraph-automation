from typing import List, Dict, Any, Hashable
import asyncio
from gql import Client

from .apollo_connector import get_apollo_client
from .query_helper.vote_events import agg_count_vote_events
from .query_helper.royal_assent_event import get_royal_assent_events, create_royal_assent_event, update_royal_assent_event
from .query_helper.enforce_event import agg_count_enforce_event, create_enforce_event # TODO remove
from .query_helper.enact_event import create_enact_event, update_enact_event
from .query_helper.reject_event import agg_count_reject_event, create_reject_event, update_reject_event
from .query_helper.draft_vote_event import agg_count_draft_vote_events, update_draft_vote_event, create_draft_vote_event # TODO remove
from .query_helper.bill_vote_event import create_bill_vote_event, update_bill_vote_event
from .query_helper.bills import get_bills, update_bill
from .query_helper.merge_event import agg_count_merge_event, create_merge_event, update_merge_event

def is_vote_event_exist_in_bill(
    bill_id: str,
    classification: str,
    vote_event_type: str='VOTE_EVENT'
) -> bool:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    param = {
        "where": {
            "classification_EQ": classification,
            "bills_SOME": {
                "id_EQ": bill_id
            }
        }
    }
    
    aggregate_handler_dispatcher = {
        'DRAFT': agg_count_draft_vote_events,
        'VOTE_EVENT': agg_count_vote_events
    }
    
    aggregate_handler = aggregate_handler_dispatcher.get(vote_event_type, None)
    if not aggregate_handler:
        raise ValueError("vote_event_type option is invalid")
    
    count_vote_event = asyncio.run(aggregate_handler(
        client=apollo_client,
        params=param
    ))
    
    return bool(count_vote_event)

def create_new_draft_vote_event(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill ID
    bill_id = bill_info.get('id', "")
    
    # Get event info
    event_type = event_info.get("event_type", "")
    msbis_id = event_info.get("msbis_id", None)
    vote_date = event_info.get("vote_date", None)
    vote_result = event_info.get("vote_result", None)
    
    # Get vote data
    vote_count_data = event_info.get("vote_count", {})
    agree_count = vote_count_data.get("agree_count", None)
    disagree_count = vote_count_data.get("disagree_count", None)
    abstain_count = vote_count_data.get("abstain_count", None)
    novote_count = vote_count_data.get("novote_count", None)
    
    # Get event classification
    event_classification_index = {
        'VOTE_EVENT_MP_1': 'MP_1',
        'VOTE_EVENT_MP_3': 'MP_3',
        'VOTE_EVENT_SENATE_1': 'SENATE_1',
        'VOTE_EVENT_SENATE_3': 'SENATE_3',
    }
    event_classification = event_classification_index.get(event_type, "MP_1")
    
    # Check if this VoteEvent exist
    if is_vote_event_exist_in_bill(
        bill_id=bill_id,
        classification=event_classification,
    ):
        # If voteEvent already exist, skip
        return
    
    # Check if draftVoteEvent exist
    if is_vote_event_exist_in_bill(
        bill_id=bill_id,
        classification=event_classification,
        vote_event_type='DRAFT'
    ):
        # Construct update param
        update_params = {
            "msbis_id_SET": msbis_id,
            "classification_SET": event_classification,
            "start_date_SET": vote_date,
            "end_date_SET": vote_date,
            "result_SET": vote_result,
            "agree_count_SET": agree_count,
            "disagree_count_SET": disagree_count,
            "abstain_count_SET": abstain_count,
            "novote_count_SET": novote_count
        }
        # Update draftVoteEvent
        asyncio.run(update_draft_vote_event(
            client=apollo_client,
            params={
                "where": {
                    "classification_EQ": event_classification,
                    "bills_SOME": {
                        "id_EQ": bill_id
                    }
                },
                "update": update_params
            }
        ))
        return
    
    # Construct create param
    asyncio.run(create_draft_vote_event(
        client=apollo_client,
        params={
            "input": [
                {
                    "title": event_type,
                    "msbis_id": msbis_id,
                    "classification": event_classification,
                    "start_date": vote_date,
                    "end_date": vote_date,
                    "result": vote_result,
                    "agree_count": agree_count,
                    "disagree_count": disagree_count,
                    "abstain_count": abstain_count,
                    "novote_count": novote_count,
                    "publish_status": "UNPUBLISHED",
                    "bills": {
                        "connect": [
                        {
                            "where": {
                                "node": {
                                    "id_EQ": bill_id
                                }
                            }
                        }
                        ]
                    }
                }
            ]
        }
    ))
    return

def create_new_royal_assent_event(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill ID
    bill_id = bill_info.get('id', "")
    
    # Get event info
    result = event_info.get("result", None)
    
    # Check if RoyalAssent event already exist in bill
    royal_events = asyncio.run(get_royal_assent_events(
        client=apollo_client,
        fields=[
            'id',
            'result'
        ],
        params={
            "where": {
                "bills_SOME": {
                    "id_EQ": bill_id
                }
            }
        }
    ))
    if royal_events:
        print(royal_events)
        # Get result
        old_result = royal_events[0]['result']
        if not old_result and result: # if exist and result is valid
            # Update royal assent event
            asyncio.run(update_royal_assent_event(
                client=apollo_client,
                params={
                    "where": {
                        "bills_SOME": {
                            "id_EQ": bill_id
                        }
                    },
                    "update": {
                        "result_SET": result,
                        "publish_status_SET": "PUBLISHED"
                    }
                }
            ))
            pass
        return
    
    params = {
        "input": [
            {
                "result": result,
                "publish_status": "PUBLISHED" if result else "UNPUBLISHED",
                "bills": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "id_EQ": bill_id
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    # Create new RoyalAssent event
    asyncio.run(create_royal_assent_event(
        client=apollo_client,
        params=params
    ))
    
def create_new_enforce_event(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill ID
    bill_id = bill_info.get('id', "")
    
    # Get enforce date
    enforce_date = event_info.get("start_date", None)
    
    # Get final title
    final_title = event_info.get("final_title", None)
    
    # Check if enforce event exist
    agg_count = asyncio.run(agg_count_enforce_event(
        client=apollo_client,
        params={
            "where": {
                "bills_SOME": {
                    "id_EQ": bill_id
                }
            }
        }
    ))
    if agg_count: # skip
        return
    
    # Create new BillEnforceEvent
    params = {
        "input": [
            {
                "title": final_title,
                "start_date": enforce_date,
                "end_date": enforce_date,
                "publish_status": "PUBLISHED",
                "bills": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "id_EQ": bill_id
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    # Create new RoyalAssent event
    asyncio.run(create_enforce_event(
        client=apollo_client,
        params=params
    ))
    
    # Update name of this bill
    update_bill_param = {
        "where": {
            "id_EQ": bill_id
        },
        "update": {
            "title_SET": final_title
        }
    }
    asyncio.run(update_bill(
        client=apollo_client,
        params=update_bill_param
    ))
    
def create_new_reject_event(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill ID
    bill_id = bill_info.get('id', None)
    if not bill_id:
        raise ValueError("Bill's ID is None")
    
    # Get enforce date
    reject_reason = event_info.get("reject_reason", None)
    
    # Check if reject event exist
    agg_count = asyncio.run(agg_count_reject_event(
        client=apollo_client,
        params={
            "where": {
                "bills_SOME": {
                    "id_EQ": bill_id
                }
            }
        }
    ))
    if agg_count: # skip
        return
    
    # Create new BillRejectEvent
    params = {
        "input": [
            {
                "reject_reason": reject_reason,
                "publish_status": "PUBLISHED",
                "bills": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "id_EQ": bill_id
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    # Create new BillRejectEvent event
    asyncio.run(create_reject_event(
        client=apollo_client,
        params=params
    ))
    
async def create_and_connect_merge_event(
    client: Client,
    merged_bill_ids: List[str]
):
    # Create new merge event
    create_param = {
        "input": [{"publish_status": "UNPUBLISHED"}]
    }
    result = await create_merge_event(
        client=client,
        params=create_param
    )
    
    new_mereg_event_id = result['createBillMergeEvents']['billMergeEvents'][0]['id']
    
    # Connect merge event to bills
    for bill_id in merged_bill_ids:
        update_param = {
            "where": {
                "id_EQ": new_mereg_event_id
            },
            "update": {
                "bills": [
                    {
                        "connect": [{
                            "where": {
                                "node": {
                                    "id_EQ": bill_id
                                }
                            }
                        }]
                    }
                ]
            }
        }
        await update_merge_event(
            client=client,
            params=update_param
        )

def create_new_merge_event(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill ID
    bill_id = bill_info.get('id', "")
    
    # Get merged bills data
    merged_bills_data = event_info.get('merged_bills', [])
    
    # Get acceptance numbers & lis_ids to query all merged bills
    merged_acceptance_numbers = [d['acceptance_number'] for d in merged_bills_data]
    merged_lis_ids = [d['lis_id'] for d in merged_bills_data]
    
    # Query all bill involve to get ID
    merged_bills = asyncio.run(get_bills(
        client=apollo_client,
        fields=['id', 'acceptance_number', 'lis_id'],
        params={
            "where": {
                "acceptance_number_IN": merged_acceptance_numbers,
                "lis_id_IN": merged_lis_ids
            }
        }
    ))
    
    # Use bill's ID to query merge event
    merged_bill_ids = [d['id'] for d in merged_bills]
    if asyncio.run(agg_count_merge_event(
        client=apollo_client,
        params={
            "where": {
                "bills_SOME": {
                    "id_IN": merged_bill_ids
                }
            }
        }
    )):
        return # skip
    
    # Create new merge event
    asyncio.run(create_and_connect_merge_event(
        client=apollo_client,
        merged_bill_ids=list(set(merged_bill_ids + [bill_id]))
    ))

def add_retract_event(
    acceptance_number: str,
    lis_id: int,
    classification: str
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill
    bills = asyncio.run(get_bills(
        client=apollo_client,
        fields=[
            'id',
            'acceptance_number',
            'title',
            'classification',
            'proposal_date',
            'status',
        ],
        params={
            'where': {
                "acceptance_number_EQ": acceptance_number,
                "lis_id_EQ": lis_id,
                "classification_EQ": classification
            }
        }
    ))
    if not bills:
        return
    
    # Check status
    bill = bills[0]
    bill_status = bill.get('status', 'ตกไป')
    if 'ตกไป' in bill_status:
        return
    
    # Add reject event to bill
    # Create new BillRejectEvent
    params = {
        "input": [
            {
                "reject_reason": "ขอถอน",
                "publish_status": "PUBLISHED",
                "bills": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "id_EQ": bill.get("id")
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    # Create new BillRejectEvent event
    asyncio.run(create_reject_event(
        client=apollo_client,
        params=params
    ))
    
async def create_bill_vote_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    for param_chunk in chunker(params, batch_size):
        await create_bill_vote_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
    
    return

async def create_bill_merge_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    for param_chunk in chunker(params, batch_size):
        await create_merge_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
    
    return

async def create_bill_royal_assent_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    for param_chunk in chunker(params, batch_size):
        await create_royal_assent_event(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
    
    return

async def create_bill_enact_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

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
        await asyncio.sleep(0.1)
    
    return

async def create_bill_reject_event_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int=5
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

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
        await asyncio.sleep(0.1)
    
    return

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
        await asyncio.sleep(0.1)
        
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
        await asyncio.sleep(0.1)
        
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
        await asyncio.sleep(0.1)
        
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
        await asyncio.sleep(0.1)
        
    return