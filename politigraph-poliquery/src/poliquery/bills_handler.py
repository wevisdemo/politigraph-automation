from typing import List, Dict, Any, Hashable
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.bills import get_bills, create_bill

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
        
        # Get other data
        url = bill_info.get('url', None)
        
        # Construct param
        create_bill_param = {
            "acceptance_number": acceptance_number,
            "classification": classification,
            "title": title,
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
    