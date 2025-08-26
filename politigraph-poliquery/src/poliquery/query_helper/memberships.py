from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_memberships(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
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
    valid_property = await get_allowed_fields_for_type(client=client, type_name='Membership')
    
    # Check if any fields in the list is invalid
    import re
    if any(re.sub(r"\s.*", "", prop) not in valid_property for prop in fields):
        raise ValueError("Invalid field name.")

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query Memberships($where: MembershipWhere, $sort: [MembershipSort!]) {{
        memberships(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['memberships']
    
async def create_membership(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($input: [MembershipCreateInput!]!) {
        createMemberships(input: $input) {
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
    
async def update_membership(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($where: MembershipWhere, $update: MembershipUpdateInput) {
        updateMemberships(where: $where, update: $update) {
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