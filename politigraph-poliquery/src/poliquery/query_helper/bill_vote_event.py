from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_bill_vote_events(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query BillVoteEvents node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of billVoteEvents data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='BillVoteEvent')
    
    # Check if any fields in the list is invalid
    import re
    if any(re.sub(r"\s.*", "", prop) not in valid_property for prop in fields):
        raise ValueError("Invalid field name.")

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query BillVoteEvents($where: BillVoteEventWhere, $sort: [BillVoteEventSort!]) {{
        billVoteEvents(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['billVoteEvents']
    
async def create_bill_vote_event(client: Client, params: dict) -> Dict[str, Any]:
    query = gql(
    """
    mutation CreateBillVoteEvents($input: [BillVoteEventCreateInput!]!) {
        createBillVoteEvents(input: $input) {
            info {
            nodesCreated
            relationshipsCreated
            }
            billVoteEvents {
                id
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result
    
async def update_draft_vote_event(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateBillVoteEvents($where: BillVoteEventWhere, $update: BillVoteEventUpdateInput) {
        updateBillVoteEvents(where: $where, update: $update) {
            info {
            nodesCreated
            nodesDeleted
            relationshipsCreated
            relationshipsDeleted
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result 
