from typing import Any
import re
from itertools import batched
from .bills import Bill

from .data_loader import (
    get_name_index,
    get_cabinet_id_with_prime_minister_name,
)
from .utilities import correct_typo
from thai_name_normalizer import remove_thai_name_prefix


def generate_create_bill_param(bill: Bill) -> dict[str, list]:
    
    # Initiate base param
    param: dict[str, Any] = {
        "title": bill.title,
        "classification": bill.classification,
        # TODO: handle multiple lis_id after updated schema
        "lis_id": bill.lis_id,
        "proposal_date": bill.proposal_date,
        "acceptance_number": bill.acceptance_number,
        "status": bill.status,
        "creator_type": "UNKNOWN"
    }
    
    # Check for proposer type
    proposer_name = bill.get_proposer_name()
    if re.search(r"คณะรัฐมนตรี", proposer_name):
        cabinet_id = get_cabinet_id_with_prime_minister_name(bill.get_prime_minister_name())
        if cabinet_id:
            creators_param = {
                "Organization": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "id": {
                                        "eq": cabinet_id
                                    }
                                }
                            }
                        }
                    ]
                }
            }
            param['creators'] = creators_param
        param['creator_type'] = "ASSEMBLY"
    elif re.search(r"ประชาชน", proposer_name): # TODO: update regex
        param['creator_type'] = "PEOPLE"
    else: # creators is person
        # Load name index
        name_index = get_name_index(bill.get_parliament_term())
        person_id = name_index.get(remove_thai_name_prefix(proposer_name))
        creators_param = {
            "Person": {
                "connect": [
                    {
                        "where": {
                            "node": {
                                "id": {
                                    "eq": person_id
                                }
                            }
                        }
                    }
                ]
            }
        }
        param['creators'] = creators_param
        param['creator_type'] = "POLITICIAN"
    
    # Connect to organization
    # สภาผู้แทนราษฎร-N
    org_id = f"สภาผู้แทนราษฎร-{bill.get_parliament_term()}"
    param['organizations'] = {
        "connect": [
            {
                "where": {
                    "node": {
                        "id": {
                            "eq": org_id
                        }
                    }
                }
            }
        ]
    }
    
    # Add link
    param['links'] = {
        "create": [
            {
                "node": {
                    "note": "ระบบสารสนเทศด้านนิติบัญญัติ",
                    "url": bill.url
                }
            }
        ]
    }
    
    # Construct create param
    create_bill_param = {
        "input": [
            param
        ]
    }
    
    return create_bill_param

def generate_co_proposer_connect_param(bill: Bill) -> list[dict[str, Any]] | None:
    
    # Get co proposer
    co_proposers: list[dict[str, str]] = bill.co_proposer
    if len(co_proposers) == 0:
        return None
    
    print(f"generate param to connect co-proposers total : {len(co_proposers)}")
    
    # Load name-ID index
    name_index = get_name_index(bill.get_parliament_term())
    
    connect_id_list = []
    for co_proposer in co_proposers:
        name = co_proposer.get("name")
        name = remove_thai_name_prefix(name) # remove prefix
        
        # Correct typo
        corrected_name = correct_typo(name, list(name_index.keys()))
        
        # Match closest name
        person_id = name_index.get(corrected_name)
        connect_id_list.append({
            "where": {
                "node": {
                    "id": {
                        "eq": person_id
                    }
                }
            }
        })

    # Split into chunks of 10
    chunks = [list(chunk) for chunk in batched(connect_id_list, 10)]
    update_params = []
    for chunk in chunks:
        update_co_proposers_param = {
            "where": {
                "id": {
                    "eq": bill.id
                }
            },
            "update": {
                "co_creators": [
                    {
                        "connect": chunk
                    }   
                ]
            }
        }
        update_params.append(update_co_proposers_param)
    
    return update_params