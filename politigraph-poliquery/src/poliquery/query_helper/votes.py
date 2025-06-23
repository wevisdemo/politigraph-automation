from gql import gql
from gql import Client

def get_vote(client: Client, params: dict):
    query = gql(
    """
    query Query($where: VoteWhere) {
        votes(where: $where) {
            id
            vote_order
            badge_number
            voter_name
            voter_party
            option
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result 

def add_vote(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($input: [VoteCreateInput!]!) {
        createVotes(input: $input) {
            info {
                nodesCreated
                relationshipsCreated
            }
            votes {
                id
            }
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result 
