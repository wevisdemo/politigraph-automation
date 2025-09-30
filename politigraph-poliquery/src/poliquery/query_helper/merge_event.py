from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_merge_events(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query BillMergeEvent node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of BillMergeEvent data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='BillMergeEvent')
    
    # Check if any fields in the list is invalid
    import re
    if any(re.sub(r"\s.*", "", prop) not in valid_property for prop in fields):
        raise ValueError("Invalid field name.")

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query BillMergeEvents($where: BillMergeEventWhere, $sort: [BillMergeEventSort!]) {{
        billMergeEvents(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['billMergeEvents']
    
async def create_merge_event(client: Client, params: dict) -> Dict[str, Any]:
    query = gql(
    """
    mutation CreateBillMergeEvents($input: [BillMergeEventCreateInput!]!) {
        createBillMergeEvents(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
            billMergeEvents {
                id
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result
    
async def update_merge_event(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateBillMergeEvents($where: BillMergeEventWhere, $update: BillMergeEventUpdateInput) {
        updateBillMergeEvents(where: $where, update: $update) {
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

async def agg_count_merge_event(client: Client, params: dict) -> int:
    query = gql(
    """
    query BillMergeEventsConnection($where: BillMergeEventWhere) {
        billMergeEventsConnection(where: $where) {
            aggregate {
                count {
                    nodes
                }
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['billMergeEventsConnection']['aggregate']['count']['nodes']