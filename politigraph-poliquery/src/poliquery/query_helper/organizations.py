from gql import gql
from gql import Client

def get_organization(client: Client, params: dict):
    query = gql(
    """
    query Query($where: OrganizationWhere) {
        organizations(where: $where) {
            id
            name
            classification
            founding_date
            dissolution_date
            term
            created_at
            updated_at
        }
    }
    """
    )
    
    result = client.execute(query, variable_values=params)
    return result

def add_organization(client: Client, params: dict):
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
    
    result = client.execute(query, variable_values=params)
    return result   

def update_organiztion(client: Client, params: dict):
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
    
    result = client.execute(query, variable_values=params)
    return result

def add_org_membership(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateOrganizations($where: OrganizationWhere, $update: OrganizationUpdateInput) {
        updateOrganizations(where: $where, update: $update) {
            info {
                nodesCreated
                relationshipsCreated
            }
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result  