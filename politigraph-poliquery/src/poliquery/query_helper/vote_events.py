from typing import List, Dict, Any
from gql import gql
from gql import Client

from deprecated import deprecated

from .schema import get_allowed_fields_for_type

async def get_vote_events(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
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
    valid_property = await get_allowed_fields_for_type(client=client, type_name='VoteEvent')
    
    # Check if any fields in the list is invalid
    if any(prop not in valid_property for prop in fields):
        return [] # TODO change to raise appropriate error

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query VoteEvents($where: VoteEventWhere, $sort: [VoteEventSort!]) {{
        voteEvents(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['voteEvents']
    
async def create_vote_event(client: Client, params: dict) -> Dict[str, Any]:
    query = gql(
    """
    mutation Mutation($input: [VoteEventCreateInput!]!) {
        createVoteEvents(input: $input) {
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

async def update_vote_event(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateVoteEvents($where: VoteEventWhere, $update: VoteEventUpdateInput) {
        updateVoteEvents(where: $where, update: $update) {
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