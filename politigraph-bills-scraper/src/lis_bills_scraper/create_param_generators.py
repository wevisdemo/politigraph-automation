from typing import Dict, Any
import os, re, json
import pickle

def create_vote_param(
    bill: Dict[str, Any],
    event: Dict[str, Any],
    assembly:str='MP',
    issue:int=1
) -> Dict[str, Any]:
    
    ############# Get info #############
    bill_id = bill.get('id', '')
    
    bill_title = bill.get('title', '')
    msbis_id = event.get('msbis_id', None)
    event_classification = assembly + "_" + str(issue)
    vote_date = event.get('start_date', None)
    vote_result = event.get('result', None)
    
    if any([event.get('session_year'), event.get('session_number'), event.get('session_type')]):
        session_identifier = "การประชุม"
        session_identifier += f" ปีที่ {event.get('session_year')}" if event.get('session_year') else ""
        session_identifier += f" {event.get('session_type')}" if event.get('session_type') else ""
        session_identifier += f" ครั้งที่ {event.get('session_number')}" if event.get('session_number') else ""
    else:
        session_identifier = None
            
    ####################################
    
    
    ############# Construct create param #############
    
    title = str(bill_title) + {
        'MP_1': ' วาระที่ 1',
        'MP_3': ' วาระที่ 3',
        'SENATE_1': ' วุฒิสภา วาระที่ 3',
        'SENATE_3': ' วุฒิสภา วาระที่ 3',
    }.get(event_classification, '')
    title = re.sub(r"\s+(วาระ|วุฒิสภา)", r" \1", title)
    
    create_param = {
        "title": title,
        "msbis_id": msbis_id,
        "classification": event_classification,
        "start_date": vote_date,
        "end_date": vote_date,
        "session_identifier": session_identifier,
        "result": vote_result,
        "publish_status": "PUBLISHED",
        "bills": {
            "connect": [
            {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill_id
                        }
                    }
                }
            }
            ]
        }
    }
    
    ####################################################
    
    
    ############# Get vote count data #############
    
    vote_count = event.get('vote_count', {})
    for vote_option in [
        "agree_count", 
        "disagree_count", 
        "abstain_count", 
        "novote_count",
    ]:
        create_param[vote_option] = vote_count.get(vote_option, None)
    
    ###############################################
    
    return create_param

def create_mp_2_param(
    bill: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]:
    
    ############# Get info #############
    bill_id = bill.get('id', '')
    
    bill_title = bill.get('title', '')
    event_classification = "MP_2"
    vote_date = event.get('start_date', None)
    vote_result = event.get('result', None)
    
    if any([event.get('session_year'), event.get('session_number'), event.get('session_type')]):
        session_identifier = "การประชุม"
        session_identifier += f" ปีที่ {event.get('session_year')}" if event.get('session_year') else ""
        session_identifier += f" {event.get('session_type')}" if event.get('session_type') else ""
        session_identifier += f" ครั้งที่ {event.get('session_number')}" if event.get('session_number') else ""
    else:
        session_identifier = None
            
    ####################################
    
    
    ############# Construct create param #############
    
    title = str(bill_title) + {
        'MP_1': ' วาระที่ 1',
        'MP_3': ' วาระที่ 3',
        'SENATE_1': ' วุฒิสภา วาระที่ 3',
        'SENATE_3': ' วุฒิสภา วาระที่ 3',
    }.get(event_classification, '')
    title = re.sub(r"\s+(วาระ|วุฒิสภา)", r" \1", title)

    create_param = {
        "title": title,
        "classification": event_classification,
        "start_date": vote_date,
        "end_date": vote_date,
        "session_identifier": session_identifier,
        "result": vote_result,
        "publish_status": "PUBLISHED",
        "bills": {
            "connect": [
            {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill_id
                        }
                    }
                }
            }
            ]
        }
    }
    
    ####################################################
    
    ################ Check & Add Links #################
    
    links = event.get('links', [])
    links_create_param = []
    if links:
        for link in links:
            links_create_param.append({
                "node": {
                    "note": link.get("note"),
                    "url": link.get("url"),
                }
            })
    
    create_param["links"] = {
        "create": links_create_param
    }
    
    ####################################################
    
    return create_param

def create_merge_param(
    bill: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]|None:
    
    # Load cache merged lis_id
    if not os.path.exists('merged_lis_id.pkl'):
        with open('merged_lis_id.pkl', 'wb') as file:
            pickle.dump([], file)
    
    with open('merged_lis_id.pkl', 'rb') as file:
        cache_lis_id = pickle.load(file)
        
    ############# Construct create param #############
    
    total_merged_bills = event.get('total_merged_bills', None)
    create_param = {
        "total_merged_bills": total_merged_bills,
        "publish_status": 'PUBLISHED',
    }
    
    # Add connection to merged bills
    merged_bills = event.get('merged_bills')
    if not merged_bills:
        return None
    # Define connect param
    connect_params = []
    # Load politigraph bill list
    with open('politigraph_bill_list.pkl', 'rb') as file:
        politigraph_bill_list = pickle.load(file)
    for merged_bill in merged_bills:
        # Check if bill already have a create merged event instruction
        if merged_bill.get('lis_id') in cache_lis_id:
            return None
        cache_lis_id.append(merged_bill.get('lis_id'))
        # Get matched bill
        matched_bill = next(
            (b for b in politigraph_bill_list\
                if b.get('lis_id') == merged_bill['lis_id']\
                and b.get('acceptance_number') == merged_bill['acceptance_number'])
            , None
        )
        if not matched_bill:
            continue
        connect_params.append({
            "where": {
                "node": {
                    "id": {
                        "eq": matched_bill.get('id')
                    }
                }
            }
        })
        
    # Add id of this bill
    connect_params.append({
        "where": {
            "node": {
                "id": {
                    "eq": bill.get('id')
                }
            }
        }
    })
    cache_lis_id.append(bill.get('lis_id'))
    
    # Add connect to main create param
    create_param['bills'] = {
        'connect': connect_params
    }
    ##################################################
    
    # Cache merged lis_id
    with open('merged_lis_id.pkl', 'wb') as file:
        pickle.dump(cache_lis_id, file)
    
    return create_param

def create_royal_assent_param(
    bill: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]|None:
    
    create_param = {
        "result": event.get('result'),
        "publish_status": 'PUBLISHED',
        "bills": {
        "connect": [
            {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill.get('id')
                        }
                    }
                }
            }
        ]
        }
    }
    
    return create_param

def create_enact_param(
    bill: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]|None:
    
    create_param = {
        "title": event.get('title'),
        "start_date": event.get('start_date'),
        "end_date": event.get('start_date'),
        "publish_status": 'PUBLISHED',
        "bills": {
            "connect": [
            {
                "where": {
                    "node": {
                        "id": {
                            "eq": bill.get('id')
                        }
                    }
                }
            }
            ]
        }
    }
    
    # Add link node if pdf file is present
    if event.get('announcement_report_link'):
        create_param['links'] = {
            "create": [
                {
                    "node": {
                        "note": "ราชกิจจานุเบกษา",
                        "url": event.get('announcement_report_link'),
                    }
                }
            ]
        }
    
    return create_param

def create_reject_param(
    bill: Dict[str, Any],
    event: Dict[str, Any],
) -> Dict[str, Any]|None:
    
    create_param = {
      "reject_reason": event.get('reject_reason'),
      "publish_status": 'PUBLISHED',
      "bills": {
            "connect": [
                {
                    "where": {
                        "node": {
                            "id": {
                                "eq": bill.get('id')
                            }
                        }
                    }
                }
            ]
        }
    }
    
    return create_param


CERATE_PARAM_DISPATCH = {
    'VOTE_EVENT_MP_1': lambda bill, event: create_vote_param(
        bill=bill,
        event=event,
        assembly='MP',
        issue=1
    ),
    'VOTE_EVENT_MP_2': lambda bill, event: create_mp_2_param(
        bill=bill,
        event=event,
    ),
    'VOTE_EVENT_MP_3': lambda bill, event: create_vote_param(
        bill=bill,
        event=event,
        assembly='MP',
        issue=3
    ),
    'VOTE_EVENT_SENATE_1': lambda bill, event: create_vote_param(
        bill=bill,
        event=event,
        assembly='SENATE',
        issue=1
    ),
    'VOTE_EVENT_SENATE_3': lambda bill, event: create_vote_param(
        bill=bill,
        event=event,
        assembly='SENATE',
        issue=3
    ),
    'MERGE': lambda bill, event: create_merge_param(
        bill=bill,
        event=event,
    ),
    'ROYAL_ASSENT': lambda bill, event: create_royal_assent_param(
        bill=bill,
        event=event,
    ),
    'ENACT': lambda bill, event: create_enact_param(
        bill=bill,
        event=event,
    ),
    'REJECT': lambda bill, event: create_reject_param(
        bill=bill,
        event=event,
    ),
}