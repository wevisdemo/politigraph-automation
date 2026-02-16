from typing import List, Dict, Any, Hashable, TypeVar
import asyncio

from thai_name_normalizer import remove_thai_name_prefix

from .apollo_connector import get_apollo_client
from .query_helper.bills import get_bills, create_bill, update_bill
from .query_helper.persons import get_persons
from .query_helper.organizations import get_organizations
from .politician_handler import get_politician_prefixes, get_representative_members_name, get_people_in_party
from .parliament_handler import get_all_house_of_representatives

from cachetools import cached, TTLCache

async def get_all_bills_info(
    parliament_terms: int
) -> List[Dict[str, Any]]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
     # Construct house of representative ID index
    hor_index = {
        h['term']: h['id'] for h in await get_organizations(
            client=apollo_client,
            fields=['id', 'name', 'term'],
            params={
                "where": {
                    "classification": {
                        "eq": "HOUSE_OF_REPRESENTATIVE"
                    }
                }
            }
        )
    }
    
    # Get latest parliament term
    param = {
        "where": {
            "organizations": {
                "some": {
                    "id": {
                        "eq": hor_index.get(parliament_terms),
                    }
                }
            }
        }
    }
    
    bill_events_field = {
        'BillVoteEvent': [
            'id', 'classification', 'start_date', 'result', \
            'msbis_id', 'session_identifier',\
            'agree_count', 'disagree_count', 'abstain_count', 'novote_count'
        ],
        'BillRoyalAssentEvent': ['id', 'result'],
        'BillMergeEvent': ['id', 'main_bill_id', 'total_merged_bills'],
        'BillRejectEvent': ['id', 'reject_reason'],
        'BillEnactEvent': ['id', 'title'],
    }
    
    bill_event_param = "bill_events {"
    for event, field in bill_events_field.items():
        bill_event_param += f" ... on {event} " + "{ " + " ".join(field + ['__typename']) + " }"
    bill_event_param += " }"
    
    query_field = [
        'id',
        'acceptance_number',
        'lis_id',
        'title',
        'classification',
        'proposal_date',
        'status',
        'links {note\nurl}',
        bill_event_param,
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
                                    "classification": {
                                        "eq": "HOUSE_OF_REPRESENTATIVE",
                                    },
                                    "id": {
                                        "eq": f"สภาผู้แทนราษฎร-{parliament_term}"
                                    }
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

# @cached(cache=TTLCache(maxsize=256, ttl=120))
async def get_prime_minister_cabinet_index(bill_proposal_date: str|None=None) -> Dict[str, str]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    param = {
        "where": {
            "memberships": {
                "some": {
                    "posts": {
                        "some": {
                            "role": {
                                "eq": "นายกรัฐมนตรี"
                            }
                        }
                    }
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
                    "classification": {
                        "eq": "CABINET",
                    },
                    "posts": {
                        "some": {
                            "role": {
                                "eq": "นายกรัฐมนตรี",
                            },
                            "memberships": {
                                "some": {
                                    "members": {
                                        "some": {
                                            "Person": {
                                                "id": {
                                                    "eq": prime_minister['id']
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                    }
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
        # print(cabinet_index)
        print(f"cabinet prime minister : {prime_minister_name}")
        creators_param['Organization'] = [
            {
                "connect": [
                    {
                        "where": {
                                "node": {
                                    "id": {
                                        "eq": cabinet_index.get(prime_minister_name, None)
                                    }
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
        
        # import json
        # print(json.dumps(repr_member_names, indent=2, ensure_ascii=False))
        
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
                                    "id": {
                                        "eq": name_index.get(proposer_name, None)
                                    }
                            }
                        }
                    }
                ]
            }
        ]
        
    update_param = {
        "proposal_date": {
            "set": proposal_date
        }
    }
    if creators_param:
        update_param['creators'] = creators_param
    
    params = {
        'where': {
            "id": {
                "eq": bill_id
            }
        },
        'update': update_param
    }
    
    # import json
    # print(json.dumps(params, indent=2, ensure_ascii=False))
    print("".join(["=" for _ in range(30)]))
    
    # Update bill info
    asyncio.run(update_bill(
        client=apollo_client,
        params=params
    ))
    
    return

def update_bill_co_proposer(
    bill_info: Dict[str, Any],
    event_info: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get bill info
    bill_id = bill_info.get('id', None)
    print(bill_id)
    
    # Get co-proposer
    co_proposers = event_info['co_proposer']
    
    # Get unique party's name
    parties_name = list(set(
        [d.get('party_name', '') for d in co_proposers]
    ))
    # Get all politician in all parties
    politicians_name = []
    for party in parties_name:
        politicians_name.extend(get_people_in_party(party_name=party))
    
    # Construct politician name-ID index
    name_id_index = { p['name']:p['id'] for p in politicians_name }
    
    # Construct update instruction
    update_inst = [
        {
            'name': remove_thai_name_prefix(c['name']),
            'id': name_id_index.get(remove_thai_name_prefix(c['name']), "")
            
        } for c in co_proposers
    ]
    
    async def update_multiple_co_proposer():
        connect_params = []
        for person in update_inst:
            connect_params.append({
                "where": {
                    "node": { 
                        "id": {
                            "eq": person['id']
                        } 
                    }
                }
            })
            if len(connect_params) >= 10:
                await update_bill(
                    client=apollo_client,
                    params={
                        "where": {
                            "id": {
                                "eq": bill_id
                            }
                        },
                        "update": {
                            "co_creators": [
                                {
                                    "connect": connect_params
                                }
                            ]
                        }
                    }
                )
                connect_params = []
                
    asyncio.run(update_multiple_co_proposer())
        
    return

def update_bill_data(
    lis_id: int, 
    acceptance_number: str,
    data: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    from .query_helper.schema import get_allowed_fields_for_type
    
    # Check validity of the field
    valid_property = asyncio.run(get_allowed_fields_for_type(client=apollo_client, type_name='Bill'))
    
    if any(key not in valid_property for key in data.keys()):
        raise KeyError("Invalid key")
    
    # Construct update param
    update_param = {}
    for key, value in data.items():
        update_param[key] = {
            "set": value
        }
    
    # Update bill info
    asyncio.run(update_bill(
        client=apollo_client,
        params={
            "where": {
                "lis_id": {
                    "eq": lis_id
                },
                "acceptance_number": {
                    "eq": acceptance_number
                }
            },
            "update": update_param
        }
    ))
 
async def create_bills_in_chunk(
    params: List[Dict[str, Any]],
    batch_size: int|None=None
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()

    T = TypeVar('T')
    def chunker(seq: List[T], size:int) -> List[List[T]]:
        return [seq[pos:pos + size] for pos in range(0, len(seq), size)]
    
    # Check & Exclude any param with long connection param
    long_params:List[Dict] = []
    if any(
        len(param.get('co_proposers', {}).get('connect', [])) > 10\
            for param in params
    ):
        long_params.extend([
            param for param in params\
                if len(param.get('co_proposers', {}).get('connect', [])) > 20
        ])
        params = [param for param in params if param not in long_params]
    
    # Create bill with short param
    for param_chunk in chunker(params, size=1):
        results = await create_bill(
            client=apollo_client,
            params={
                'input': param_chunk
            }
        )
        for bill in results.get('createBills', {}).get('bills', []):
            print(f"Created bill : {bill.get('id')}")
            
        await asyncio.sleep(5)
        # pass
        
    # Create bill with long param
    print("🚧 Starting create bills with long param...")
    for param in long_params:
        # Get all co-proposer param
        co_proposer_conn = param.get('co_proposers', {}).get('connect', [])
        
        # Pull only first 5 connection to create
        _first_five = co_proposer_conn[:5]
        co_proposer_conn = co_proposer_conn[5:] # remove first 5 connects
        
        import json
        # Create bill
        param['co_proposers']['connect'] = _first_five
        results = await create_bill(
            client=apollo_client,
            params={
                'input': [param]
            }
        )
        await asyncio.sleep(3)
        
        # Get bill's ID
        bills = results.get('createBills', {}).get('bills', [])
        if not bills:
            continue
        bill_id = bills[0].get('id')
        print(f"Created bill : {bill_id}")
        
        # Update connection
        for connect_chunk in chunker(co_proposer_conn, size=5):
            
            await update_bill(
                client=apollo_client,
                params={
                    "where": {
                        "id": {
                            "eq": bill_id
                        }
                    },
                    "update": {
                        "co_creators": [{
                            "connect": connect_chunk
                        }]
                    }
                }
            )
            print(f"\tAdded bill's co-proposers total : {len(connect_chunk)} people")
            await asyncio.sleep(3)
    
    return