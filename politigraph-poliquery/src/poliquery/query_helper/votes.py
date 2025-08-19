from typing import List, Dict, Any
from gql import gql
from gql import Client

from deprecated import deprecated

from .schema import get_allowed_fields_for_type

async def get_votes(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query VoteEvents node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of voteEvents data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='Vote')
    
    # Check if any fields in the list is invalid
    if any(prop not in valid_property for prop in fields):
        return [] # TODO change to raise appropriate error

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query Votes($where: VoteWhere, $sort: [VoteSort!]) {{
        votes(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['votes']
    
async def create_votes(client: Client, params: dict) -> Dict[str, Any]:
    query = gql(
    """
    mutation CreateVotes($input: [VoteCreateInput!]!) {
        createVotes(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
            voteEvents {
                id
            }
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result

async def update_votes(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateVotes($where: VoteWhere, $update: VoteUpdateInput) {
        updateVotes(where: $where, update: $update) {
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
    
async def delete_votes(client: Client, params: dict):
    query = gql(
    """
    mutation DeleteVotes($where: VoteWhere) {
        deleteVotes(where: $where) {
            nodesDeleted
            relationshipsDeleted
        }
    }
    """
    )
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result 