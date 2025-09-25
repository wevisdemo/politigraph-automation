from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_royal_assent_events(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query BillRoyalAssentEvents node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of BillRoyalAssentEvents data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='BillRoyalAssentEvent')
    
    # Check if any fields in the list is invalid
    import re
    if any(re.sub(r"\s.*", "", prop) not in valid_property for prop in fields):
        raise ValueError("Invalid field name.")

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query BillRoyalAssentEvents($where: BillRoyalAssentEventWhere, $sort: [BillRoyalAssentEventSort!]) {{
        billRoyalAssentEvents(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['billRoyalAssentEvents']
    
async def create_royal_assent_event(client: Client, params: dict) -> Dict[str, Any]:
    query = gql(
    """
    mutation Mutation($input: [BillRoyalAssentEventCreateInput!]!) {
        createBillRoyalAssentEvents(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
            billRoyalAssentEvents {
                id
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result
    
async def update_royal_assent_event(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateBillRoyalAssentEvents($where: BillRoyalAssentEventWhere, $update: BillRoyalAssentEventUpdateInput) {
        updateBillRoyalAssentEvents(where: $where, update: $update) {
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
    
async def agg_count_royal_assent_events(client: Client, params: dict) -> int:
    query = gql(
    """
    query BillRoyalAssentEventsConnection {
        billRoyalAssentEventsConnection {
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
        return result['billRoyalAssentEventsConnection']['aggregate']['count']['nodes']