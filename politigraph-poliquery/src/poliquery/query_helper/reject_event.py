from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_reject_events(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query BillRejectEvents node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of BillRejectEvents data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='BillRejectEvent')
    
    # Check if any fields in the list is invalid
    import re
    if any(re.sub(r"\s.*", "", prop) not in valid_property for prop in fields):
        raise ValueError("Invalid field name.")

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query BillRejectEvents($where: BillRejectEventWhere, $sort: [BillRejectEventSort!]) {{
        billRejectEvents(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['billRejectEvents']
    
async def create_reject_event(client: Client, params: dict) -> Dict[str, Any]:
    query = gql(
    """
    mutation CreateBillRejectEvents($input: [BillRejectEventCreateInput!]!) {
        createBillRejectEvents(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
            billRejectEvents {
                id
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result
    
async def update_reject_event(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateBillRejectEvents($where: BillRejectEventWhere, $update: BillRejectEventUpdateInput) {
        updateBillRejectEvents(where: $where, update: $update) {
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

async def agg_count_reject_event(client: Client, params: dict) -> int:
    query = gql(
    """
    query Query($where: BillRejectEventWhere) {
        billRejectEventsConnection(where: $where) {
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
        return result['billRejectEventsConnection']['aggregate']['count']['nodes']
    
async def delete_reject_event(client: Client, params: dict) -> None:
    query = gql(
    """
    mutation Mutation($where: BillRejectEventWhere) {
        deleteBillRejectEvents(where: $where) {
            nodesDeleted
            relationshipsDeleted
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  