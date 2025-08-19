from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_persons(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query Person node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of people data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='Person')
    
    # Check if any fields in the list is invalid
    if any(prop not in valid_property for prop in fields):
        return [] # TODO change to raise appropriate error

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query Query($where: PersonWhere, $sort: [PersonSort!]) {{
        people(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['people']

async def create_person(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($input: [PersonCreateInput!]!) {
        createPeople(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
        }
    }
    """
    )

    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result   
    
async def update_person(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($update: PersonUpdateInput, $where: PersonWhere) {
        updatePeople(update: $update, where: $where) {
            info {
                nodesCreated
                relationshipsCreated
            }
        }
    }
    """
    )

    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result    