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