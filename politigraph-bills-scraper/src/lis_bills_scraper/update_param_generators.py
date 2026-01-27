from typing import Dict, Any
import os, re, json

def update_vote_param(
    event: Dict[str, Any],
) -> Dict[str, Any]:
    
    ############# Get info #############
    update_data = {
        'msbis_id': event.get('msbis_id', None),
        'start_date': event.get('start_date', None),
        'end_date': event.get('start_date', None),
        'result': event.get('result', None),
    }
    
    if any([event.get('session_year'), event.get('session_number'), event.get('session_type')]):
        session_identifier = "การประชุม"
        session_identifier += f" ปีที่ {event.get('session_year')}" if event.get('session_year') else ""
        session_identifier += f" {event.get('session_type')}" if event.get('session_type') else ""
        session_identifier += f" ครั้งที่ {event.get('session_number')}" if event.get('session_number') else ""
    else:
        session_identifier = None
    update_data['session_identifier'] = session_identifier
            
    ####################################
    
    ############# Construct update param #############
    update_param = {}
    for key, value in update_data.items():
        if value:
            update_param[key] = {
                "set": value
            }
            
    # Add vote count
    for vote_option, vote_count in event.get('vote_count', {}).items():
        update_param[vote_option] = {
            "set": vote_count
        }
    
    result_param = {
        'where': {
            'id': {
                "eq": event.get('id')
            }
        },
        'update': update_param
    }   
    
    return result_param

def update_royal_assent_param(
    event: Dict[str, Any],
) -> Dict[str, Any]:
    
    ############# Get info #############
    result = event.get('result')
    
    ############# Construct update param #############
    result_param = {
        'where': {
            'id': {
                "eq": event.get('id')
            }
        },
        'update': {
            'result': {
                "set": result
            }
        }
    }
    
    return result_param

def update_enact_param(
    event: Dict[str, Any],
) -> Dict[str, Any]:
    
    ############# Get info #############
    title = event.get('title')
    
    ############# Construct update param #############
    result_param = {
        'where': {
            'id': {
                "eq": event.get('id')
            }
        },
        'update': {
            'title': {
                "set": title
            }
        }
    }
    
    return result_param

def update_reject_param(
    event: Dict[str, Any],
) -> Dict[str, Any]:
    
    ############# Get info #############
    reject_reason = event.get('reject_reason')
    
    ############# Construct update param #############
    result_param = {
        'where': {
            'id': {
                "eq": event.get('id')
            }
        },
        'update': {
            'reject_reason': {
                "set": reject_reason
            }
        }
    }
    
    return result_param
    
UPDATE_PARAM_DISPATCH = {
    'VOTE_EVENT_MP_1': lambda event: update_vote_param(
        event=event,
    ),
    'VOTE_EVENT_MP_3': lambda event: update_vote_param(
        event=event,
    ),
    'VOTE_EVENT_SENATE_1': lambda event: update_vote_param(
        event=event,
    ),
    'VOTE_EVENT_SENATE_3': lambda event: update_vote_param(
        event=event,
    ),
    'ROYAL_ASSENT': lambda event: update_royal_assent_param(
        event=event,
    ),
    'ENACT': lambda event: update_enact_param(
        event=event,
    ),
    'REJECT': lambda event: update_reject_param(
        event=event,
    ),
}
    