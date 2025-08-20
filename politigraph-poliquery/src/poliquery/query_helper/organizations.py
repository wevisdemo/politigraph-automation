from typing import List, Dict, Any
from gql import gql
from gql import Client

from .schema import get_allowed_fields_for_type

async def get_organizations(client:Client, fields:List[str], params:Dict={}) -> List[Dict[str, Any]]:
    """
    Query Organizations node data with given fields.

    Args:
        client: gql.Client
            The GQL client with a fetched schema.
        fields: list
            Field of data to query.
        params: dict, optional
            Dictionary object of query parameter.

    Returns:
        A list of organizations data.
    """
    
    # Load schema to get valid fields
    valid_property = await get_allowed_fields_for_type(client=client, type_name='Organization')
    
    # Check if any fields in the list is invalid
    import re
    if any(re.sub(r"\s.*", "", prop) not in valid_property for prop in fields):
        raise ValueError("Invalid field name.")

    fields_string = "\n            ".join(fields)
    query_string = f"""
    query Organizations($where: OrganizationWhere, $sort: [OrganizationSort!]) {{
        organizations(where: $where, sort: $sort) {{
            {fields_string}
        }}
    }}
    """
    query = gql(query_string)
    async with client as session:
        result = await session.execute(query, variable_values=params)  
        return result['organizations']
    
async def create_organization(client: Client, params: dict):
    query = gql(
    """
    mutation CreateOrganizations($input: [OrganizationCreateInput!]!) {
        createOrganizations(input: $input) {
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

async def update_organiztion(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($where: OrganizationWhere, $update: OrganizationUpdateInput) {
        updateOrganizations(where: $where, update: $update) {
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