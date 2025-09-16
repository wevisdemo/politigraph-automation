from typing import List, Dict, Any, Hashable
import asyncio

from thai_name_normalizer import remove_thai_name_prefix

from .apollo_connector import get_apollo_client
from .query_helper.bills import get_bills, create_bill, update_bill
from .query_helper.persons import get_persons
from .query_helper.organizations import get_organizations
from .politician_handler import get_politician_prefixes, get_representative_members_name

from cachetools import cached, TTLCache

async def get_all_bills_info(
    parliament_terms: int
) -> List[Dict[str, Any]]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get latest parliament term
    param = {
        "where": {
            "organizations_SOME": {
            "id_EQ": f"สภาผู้แทนราษฎร-{parliament_terms}"
            }
        }
    }
    
    query_field = [
        'id',
        'acceptance_number',
        'title',
        'classification',
        'proposal_date',
        'result',
        'links {note\nurl}'
    ]
    
    bills = await get_bills(
        client=apollo_client,
        fields=query_field,
        params=param
    )
    
    return bills

def create_new_multiple_bills(
    bill_data: List[Dict[Hashable, Any]],
    parliament_term: int =26,
    batch_max: int=5
) -> List[str]:
    """
    Add new bills

    Args:
        bill_data: List[Dict[Hashable, Any]]
            data of bill
        batch_max: int @optional
            The max amount of bills create in ONE query
    """
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    def generate_create_param(
        bill_info: Dict[Hashable, Any],
    ) -> Dict[str, Any]:
    
        # Get all input data
        acceptance_number = bill_info.get('acceptance_number', None)
        classification = bill_info.get('classification', None)
        title = bill_info.get('title', None)
        lis_id = bill_info.get('lis_doc_id', None)
        
        # Get other data
        url = bill_info.get('url', None)
        
        # Construct param
        create_bill_param = {
            "acceptance_number": acceptance_number,
            "classification": classification,
            "title": title,
            "lis_id": lis_id,
            "organizations": {
                "connect": [{
                            "where": {
                                "node": {
                                    "classification_EQ": "HOUSE_OF_REPRESENTATIVE",
                                    "id_EQ": f"สภาผู้แทนราษฎร-{parliament_term}"
                                }
                            }
                        }]
            },
            "links": {
                "create": [
                    {
                        "node": {
                            "note": 'ระบบสารสนเทศด้านนิติบัญญัติ',
                            "url": url
                        }
                    }
                ]
                }
            }
        return create_bill_param
    
    async def batch_create_bills(
        bill_data: List[Dict[Hashable, Any]]
    ) -> List[str]:
        
        result_ids = []
        
        # Create new votes & connect it to VoteEvent in a batch
        batch_count = 0
        create_bills_params = []
        for bill in bill_data:
            if batch_count >= batch_max:
                param = {
                    "input": create_bills_params
                }
                result = await create_bill(
                    client=apollo_client, 
                    params=param
                )
                # Get all result ids
                _ids = [b['id'] for b in result["createBills"]["bills"]]
                result_ids.extend(_ids)
                
                # Reset batch param
                batch_count = 0
                create_bills_params = []
                
            new_param = generate_create_param(bill)
            create_bills_params.append(new_param)
            batch_count += 1
        
        # Left over param
        if create_bills_params:
            param = {
                "input": create_bills_params
            }
            result = await create_bill(
                client=apollo_client, 
                params=param
            )
            # Get all result ids
            _ids = [b['id'] for b in result["createBills"]["bills"]]
            result_ids.extend(_ids)
        
        return result_ids

    bill_ids = asyncio.run(batch_create_bills(bill_data=bill_data))
    return bill_ids

@cached(cache=TTLCache(maxsize=256, ttl=120))
async def get_prime_minister_cabinet_index(bill_proposal_date: str|None) -> Dict[str, str]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    param = {
        "where": {
            "memberships_SOME": {
                # "start_date_LTE": bill_proposal_date,
                # "end_date_GTE": bill_proposal_date,
                "posts_SOME": {
                    "role_EQ": "นายกรัฐมนตรี"
                }
            }
        }
    }
    
    # Get prime minister names
    prime_ministers = await get_persons(
        client=apollo_client,
        fields=[
            'id', 'name'
        ],
        params=param
    )
    
    # Get cabinet from list of prime minister
    cabinets_index = {}
    for prime_minister in prime_ministers:
        cabinets = await get_organizations(
            client=apollo_client,
            fields=[
                'id', 'name'
            ],
            params={
                "where": {
                    "classification_EQ": "CABINET",
                    "founding_date_LTE": bill_proposal_date,
                    "dissolution_date_GT": bill_proposal_date,
                    "posts_SOME": {
                        "role_EQ": "นายกรัฐมนตรี",
                        "memberships_SOME": {
                            "members_SOME": {
                                "Person": {
                                    "id_EQ": prime_minister['id']
                                }
                            }
                        }
                    },
                }
            }
        )
        if not cabinets:
            continue
        # Add id of cabinet to dict
        cabinets_index[prime_minister['name']] = cabinets[0]['id']
    
    return cabinets_index
    
def update_bill_info(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    # Check proposal_date
    proposal_date = bill_info.get('proposal_date', None)
    if proposal_date: # already updated
        return
    
    # Get bill info
    bill_id = bill_info.get('id', None)
    
    # Get event info
    proposer = event_info.get('proposer')
    proposal_date = event_info.get('proposal_date', "")
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Construct update param
    # Get prefixes
    # Run the blocking synchronous function get_politician_prefixes in a separate thread
    politician_prefixes = get_politician_prefixes()
    
    # Check proposer
    creators_param = {}
    if proposer == 'คณะรัฐมนตรี': # proposer is cabinet
        # Get prime minister name
        prime_minister_name = event_info.get('prime_minister', "")
        prime_minister_name = remove_thai_name_prefix(
            name=prime_minister_name,
            prefixes=politician_prefixes
        )
        
        # Get prime minister index
        cabinet_index = asyncio.run(get_prime_minister_cabinet_index(
            bill_proposal_date=proposal_date
        ))
        print(cabinet_index)
        print(f"cabinet prime minister : {prime_minister_name}")
        creators_param['Organization'] = [
            {
                "connect": [
                    {
                        "where": {
                                "node": {
                                    "id_EQ": cabinet_index.get(prime_minister_name, None)
                            }
                        }
                    }
                ]
            }
        ]
    elif proposer: # proposer is a member of representatives
        parliament_term = event_info.get("parliament_term", 0)
        # Get politician names
        repr_member_names = get_representative_members_name(
            parliament_term=parliament_term
        )
        
        import json
        print(json.dumps(repr_member_names, indent=2, ensure_ascii=False))
        
        name_index = {
            p['name']: p['id'] for p in repr_member_names
        }
        
        proposer_name = remove_thai_name_prefix(
            name=proposer,
            prefixes=politician_prefixes
        )
        
        print(f"proposed by : {proposer_name}")
        creators_param['Person'] = [
            {
                "connect": [
                    {
                        "where": {
                                "node": {
                                    "id_EQ": name_index.get(proposer_name, None)
                            }
                        }
                    }
                ]
            }
        ]
        
    update_param = {
        "proposal_date_SET": proposal_date
    }
    if creators_param:
        update_param['creators'] = creators_param
    
    params = {
        'where': {
            "id_EQ": bill_id
        },
        'update': update_param
    }
    
    import json
    print(json.dumps(params, indent=2, ensure_ascii=False))
    print("".join(["=" for _ in range(30)]))
    
    # Update bill info
    asyncio.run(update_bill(
        client=apollo_client,
        params=params
    ))
    
    return
