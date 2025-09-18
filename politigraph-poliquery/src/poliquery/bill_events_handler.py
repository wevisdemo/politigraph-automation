from typing import List, Dict, Any, Hashable
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.vote_events import agg_count_vote_events
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

# TODO Handle both MP & Senate voteEvents
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
    agree_count = event_info.get("agree_count", None)
    disagree_count = event_info.get("disagree_count", None)
    abstain_count = event_info.get("abstain_count", None)
    novote_count = event_info.get("novote_count", None)
    
    print(f"bill ID : {bill_id}")
    import json
    print(json.dumps(
        event_info,
        indent=2,
        ensure_ascii=False
    ))
    
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
        # If voteEvent or draftVoteEvent already exist, skip
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