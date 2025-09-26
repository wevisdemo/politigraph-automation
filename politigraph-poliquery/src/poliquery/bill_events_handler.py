from typing import List, Dict, Any, Hashable
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.vote_events import agg_count_vote_events
from .query_helper.royal_assent_event import get_royal_assent_events, create_royal_assent_event, update_royal_assent_event
from .query_helper.enforce_event import agg_count_enforce_event, create_enforce_event
from .query_helper.draft_vote_event import agg_count_draft_vote_events, update_draft_vote_event, create_draft_vote_event

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
            "motions_SOME": {
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
    
    print(f"bill ID : {bill_id}")
    
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
                    "motions_SOME": {
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
                    "motions": {
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
                "motions_SOME": {
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
                        "motions_SOME": {
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
                "motions": {
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
                "motions_SOME": {
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
                "motions": {
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