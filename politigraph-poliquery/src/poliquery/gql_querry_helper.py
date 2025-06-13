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

def add_bill(client: Client, params: dict):
    query = gql(
    """
    mutation CreateBills($input: [BillCreateInput!]!) {
        createBills(input: $input) {
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

def update_bill(client: Client, params: dict):
    query = gql(
    """
    mutation UpdateBills($where: BillWhere, $update: BillUpdateInput) {
        updateBills(where: $where, update: $update) {
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