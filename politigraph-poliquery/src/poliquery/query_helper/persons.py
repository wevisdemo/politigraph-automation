from gql import gql
from gql import Client

def add_person(client: Client, params: dict):
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
    
    result = client.execute(query, variable_values=params)  
    return result    

def add_person_membership(client: Client, params: dict):
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
    result = client.execute(query, variable_values=params)  
    return result  

def get_people_prefixes(client: Client):
    query = gql(
    """
    query People {
        people {
            prefix
        }
    }
    """
    )
    result = client.execute(query)  
    return result

def get_people_names(client: Client, params: dict):
    query = gql(
    """
    query Query {
        people {
            name
            firstname
            lastname
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result

def agg_count_people(client: Client, params: dict):
    query = gql(
    """
    query PeopleConnection($where: PersonWhere) {
        peopleConnection(where: $where) {
            aggregate {
            count {
                    nodes
                }
            }
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result

def update_image_url(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($where: PersonWhere, $update: PersonUpdateInput) {
        updatePeople(where: $where, update: $update) {
            people {
                prefix
                firstname
                lastname
                image
            }
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result