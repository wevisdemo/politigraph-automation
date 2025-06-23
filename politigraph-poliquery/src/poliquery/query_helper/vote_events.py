from gql import gql
from gql import Client

def get_vote_event_msbis_id(client: Client, params: dict):
    query = gql(
    """
    query VoteEvents($limit: Int, $sort: [VoteEventSort!], $where: VoteEventWhere) {
        voteEvents(limit: $limit, sort: $sort, where: $where) {
            msbis_id
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result

def add_vote_event(client: Client, params: dict):
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
    result = client.execute(query, variable_values=params)  
    return result 

def update_vote_event(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateVoteEvents($where: VoteEventWhere, $update: VoteEventUpdateInput) {
        updateVoteEvents(where: $where, update: $update) {
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

def delete_votes_in_vote_event(client: Client, params: dict):
    query = gql(
    """
    mutation Mutation($where: VoteWhere) {
        deleteVotes(where: $where) {
            nodesDeleted
            relationshipsDeleted
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result 

def get_vote_event_validation_data(client: Client, params: dict):
    query = gql(
    """
    query VoteEvents($where: VoteEventWhere) {
        voteEvents(where: $where) {
            agree_count
            disagree_count
            abstain_count
            novote_count
            publish_status
        }
    }
    """
    )
    result = client.execute(query, variable_values=params)  
    return result 