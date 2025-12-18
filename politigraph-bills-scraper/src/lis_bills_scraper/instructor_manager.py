from typing import List, Dict, Any
import os, json, re
import pickle

from thai_name_normalizer import remove_thai_name_prefix
from .create_param_generators import CERATE_PARAM_DISPATCH
from .update_param_generators import UPDATE_PARAM_DISPATCH

from poliquery import get_all_house_of_representatives

def get_co_proposer_param(co_proposer: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    with open('name_index.pkl', 'rb') as file:
        name_index = pickle.load(file)
    
    result = []
    for proposer in co_proposer:
        result.append({
            "where": {
              "node": {
                "id_EQ": name_index.get(
                    remove_thai_name_prefix(proposer.get('name', ''))
                )
              }
            }
          })
    return result

def add_new_bill_instruction(
    bill: Dict[str, Any],
) -> None:
    
    # Check if create_bill_instructor.json exist
    if not os.path.exists('create_bill_instruction.pkl'):
        with open('create_bill_instruction.pkl', 'wb') as file:
            pickle.dump([], file)
            
    # Load instructor data
    with open('create_bill_instruction.pkl', 'rb') as file:
        create_instructors = pickle.load(file)
        
    # Get events from bill data
    events = bill.get('bill_events', [])
        
    # Construct bsae create new bill parameter
    create_param = {
        "title": bill.get('title', 'PLACE HOLDER'),
        "acceptance_number": bill.get('acceptance_number', None),
        "lis_id": bill.get('lis_id', None),
        "classification": bill.get('classification', None),
        "status": "IN_PROGRESS",
        "links": {
            "create": [
                {
                    "node": {
                        "note": 'ระบบสารสนเทศด้านนิติบัญญัติ',
                        "url": bill.get('url')
                    }
                }
            ]
        }
    }

    ############# Add general info #############
    info_event = next(
        (e for e in events\
            if e.get('event_type') == 'GENERAL_INFO')
        , None
    )
    if not info_event: # no info event don't create yet
        return
    
    # Check if is it a test bill
    if info_event.get('recipient') and info_event.get('recipient') == 'admin':
        print(f"Test bill detected!! {bill.get('title')}")
        return
    
    # Add proposed_date
    proposed_date = info_event.get('proposal_date', None)
    if not proposed_date: # no proposed_date don't create yet
        return
    create_param['proposal_date'] = proposed_date
    
    # Add organoztion
    # Construct house of representative ID index
    hor_index = {
        h['term']: h['id'] for h in get_all_house_of_representatives()
    }
    parliament_term = info_event.get('parliament_term')
    create_param['organizations'] = {
        "connect": [{
            "where": {
                "node": {
                    "classification_EQ": "HOUSE_OF_REPRESENTATIVE",
                    "id_EQ": hor_index.get(parliament_term),
                }
            }
        }]
    }
    
    # Add creator
    proposer = info_event.get('proposer')
    # Check if creator is person
    if proposer != "คณะรัฐมนตรี":
        with open('name_index.pkl', 'rb') as file:
            name_index = pickle.load(file)
        create_param['creators'] = {
            "Person": {
                "connect": [
                    {
                        "where": {
                            "node": {
                                "id_EQ": name_index.get(
                                    remove_thai_name_prefix(proposer)
                                )
                            }
                        }
                    }
                ]
            }
        }
    else:
        with open('prime_minister_index.pkl', 'rb') as file:
            prime_minister_index = pickle.load(file)
        prime_miniter_name = info_event.get('prime_minister', '')
        create_param['creators'] = {
            "Organization": {
                "connect": [
                    {
                        "where": {
                            "node": {
                                "id_EQ": prime_minister_index.get(
                                    remove_thai_name_prefix(
                                        prime_miniter_name
                                    )
                                )
                            }
                        }
                    }
                ]
            }
        }
        
    ############################################
    
    
    
    ############# Add co-proposer #############
    _co_proposer_events = [
        e for e in events if e['event_type'] == 'CO_PROPOSER'
    ]
    if _co_proposer_events:
        co_proposer_event = _co_proposer_events[0]
        co_proposers = co_proposer_event.get('co_proposer', [])
        create_param['co_proposers'] = {
            "connect": get_co_proposer_param(co_proposers)
        }
    ############################################
        
        
    # Update & Save create param to instructor
    create_instructors.append(
        create_param
    )
    with open('create_bill_instruction.pkl', 'wb') as file:
        pickle.dump(create_instructors, file)
        
    return

def add_new_events_instruction(
    bill: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> None:
    
    for event in events:
        event_type = event.get('event_type', '')
        create_event_handler = CERATE_PARAM_DISPATCH.get(event_type, None)
        if not create_event_handler:
            continue
        create_param = create_event_handler(
            bill=bill,
            event=event
        )
        if not create_param:
            continue
        
        # Load instructor data of that type
        instruction_filename = f"create_bill_events_instruction_{event.get('__typename', '')}.pkl"
        with open(instruction_filename, 'rb') as file:
            create_bill_events_instruction = pickle.load(file)
        
        # Update create param to instructor
        create_bill_events_instruction.append(create_param)
    
        # Save create param to instructor file
        with open(instruction_filename, 'wb') as file:
            # json.dump(create_bill_events_instruction, file, indent=4, ensure_ascii=False)
            pickle.dump(create_bill_events_instruction, file)
            
    # Check for special REJECTED status
    # ขอถอน
    if bill.get('result') == 'ขอถอน':
        
        event_typename = 'BillRejectEvent'
        
        # Load instructor data of that type
        instruction_filename = f"create_bill_events_instruction_{event_typename}.pkl"
        with open(instruction_filename, 'rb') as file:
            create_bill_events_instruction = pickle.load(file)
        # Update create param to instructor
        create_bill_events_instruction.append({
            "reject_reason": "ขอถอน",
            "publish_status": "PUBLISHED",
            "bills": {
                "connect": [
                    {
                        "where": {
                            "node": {
                                "id_EQ": bill.get('id')
                            }
                        }
                    }
                ]
            }
        })
    
        # Save create param to instructor file
        with open(instruction_filename, 'wb') as file:
            # json.dump(create_bill_events_instruction, file, indent=4, ensure_ascii=False)
            pickle.dump(create_bill_events_instruction, file)
    
    return

def add_update_events_instruction(
    bill: Dict[str, Any],
    events: List[Dict[str, Any]],
) -> None:
    
    for event in events:
        
        event_type = event.get('event_type', '')
        update_event_handler = UPDATE_PARAM_DISPATCH.get(event_type, None)
        if not update_event_handler:
            continue
        update_param = update_event_handler(
            event=event
        )
        if not update_param:
            continue
        
        # Load instructor data of that type
        instruction_filename = f"update_bill_events_instruction_{event.get('__typename', '')}.pkl"
        with open(instruction_filename, 'rb') as file:
            update_bill_events_instruction = pickle.load(file)
        
        # Update create param to instructor
        update_bill_events_instruction.append(update_param)
    
        # Save create param to instructor file
        with open(instruction_filename, 'wb') as file:
            # json.dump(create_bill_events_instruction, file, indent=4, ensure_ascii=False)
            pickle.dump(update_bill_events_instruction, file)
    
    return