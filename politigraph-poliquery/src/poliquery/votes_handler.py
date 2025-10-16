import asyncio
from typing import List, Dict, Any, Sequence

from gql import Client

from .apollo_connector import get_apollo_client
from .query_helper.vote_events import get_vote_events, update_vote_event
from .query_helper.persons import get_persons
from .query_helper.votes import get_votes, delete_votes, update_votes

################################ VALIDATION DATA ################################

def get_validation_data(vote_event_id: str) -> Dict[str, Any]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    agg_param = {
        "where": {
            "id_EQ": vote_event_id
        }
    }
    matched_vote_events = asyncio.run(get_vote_events(
        apollo_client,
        fields=[
            'agree_count',
            'disagree_count',
            'abstain_count',
            'novote_count'
        ],
        params=agg_param
    ))
    if len(matched_vote_events) == 0:
        print(f"No VoteEvent id: {vote_event_id}")
        return {}
    return matched_vote_events[0]

def update_vote_event_validation_data(
    vote_event_id: str, 
    validation_data: Dict[str, int], 
    publish_status: str|None=None,
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get data
    agree_count = validation_data.get("เห็นด้วย", -1) 
    disagree_count = validation_data.get("ไม่เห็นด้วย", -1) 
    abstained_count = validation_data.get("งดออกเสียง", -1) 
    novoted_count = validation_data.get("ไม่ลงคะแนนเสียง", -1) 
    
    if publish_status not in ["ERROR", "PUBLISHED"]:
        publish_status = "ERROR"
        
    update_vote_event_param = {
        "where": {
            "id_EQ": vote_event_id
        },
        "update": {
            "agree_count_SET": agree_count,
            "disagree_count_SET": disagree_count,
            "abstain_count_SET": abstained_count,
            "novote_count_SET": novoted_count,
            "publish_status_SET": publish_status
        }
    }
    
    asyncio.run(update_vote_event(
        client=apollo_client,
        params=update_vote_event_param
    ))

################################ VOTES DATA ################################

def get_votes_from_vote_event(
    vote_event_id: str,
) -> List[Dict[str, Any]]:
    """
    Get votes data from voteEvent

    Args:
        vote_event_id: str
            voteEvent's ID
    """
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    votes = asyncio.run(get_votes(
        client=apollo_client,
        fields=['id', 'vote_order', 'badge_number', 'voter_name', 'voter_party', 'option'],
        params={
            "where": {
                "vote_events_SOME": {
                   "id_EQ": vote_event_id
                }
            }
        }
    ))
    
    return votes

def add_votes_to_vote_event(
    vote_event_id: str,
    vote_logs: List[Dict[str, Any]],
    batch_max: int=5
) -> None:
    """
    Add new votes to voteEvent

    Args:
        vote_event_id: str
            voteEvent's ID
        vote_logs: List[Dict[str, Any]]
            List of votes info
        batch_max: int @optional
            The max amount of votes create in ONE query
    """
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get politician names
    # Construct param
    get_politician_param = {
        "where": {
            "memberships_SOME": {
                "posts_SOME": {
                    "organizations_SOME": {
                        "events_SOME": {
                            "id_EQ": vote_event_id
                        }
                    }
                }
            }
        }
    }
    
    politicians = asyncio.run(get_persons(
        client=apollo_client,
        fields=[
            'id',
            'name',
            'firstname',
            'middlename',
            'lastname'
        ],
        params=get_politician_param
    ))
    
    # Construct name index
    name_index = { d['name']: d for d in politicians }
    
    def generate_create_param(
        vote_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        
        name = vote_info.get("ชื่อ - สกุล", "") 
        param = {
              "vote_order": str(vote_info.get("ลําดับที่", "0")),
              "badge_number": str(vote_info.get("เลขที่บัตร", "x")),
              "voter_name": name,
              "voter_party": vote_info.get("ชื่อสังกัด", ""),
              "option": vote_info.get("ผลการลงคะแนน", "x")
            }

        # Check if name matched with politician in politigraph
        matched_politician = name_index.get(name, None)
        if matched_politician:
            param["voters"] = {
                "connect": [{
                    "where": {
                        "node": {
                            "id_EQ": matched_politician['id']
                        }
                    }
                  }]
            }
        
        return param
    
    async def update_votes_in_vote_event() -> None:
        
        # Create new votes & connect it to VoteEvent in a batch
        batch_count = 0
        create_params = []
        for vote in vote_logs:
            if batch_count >= batch_max:
                update_vote_event_param = {
                    "where": {
                        "id_EQ": vote_event_id
                    },
                    "update": {
                        "votes": [{
                                "create": [{"node": create_param} for create_param in create_params]
                            }]
                    }
                }
                await update_vote_event(
                    client=apollo_client,
                    params=update_vote_event_param
                )
                
                batch_count = 0
                create_params = []
            
            new_param = generate_create_param(vote)
            create_params.append(new_param)
            batch_count += 1
        
        # Check & Update left over votes
        if create_params:
            update_vote_event_param = {
                "where": {
                    "id_EQ": vote_event_id
                },
                "update": {
                    "votes": [{
                            "create": [{"node": create_param} for create_param in create_params]
                        }]
                }
            }
            await update_vote_event(
                client=apollo_client,
                params=update_vote_event_param
            )
        
    asyncio.run(update_votes_in_vote_event())
    
def replace_votes_in_vote_event(
    vote_event_id: str,
    vote_logs: List[Dict[str, Any]],
    batch_max: int=5
) -> None:
    """
    Replace votes in voteEvent with a new set of data

    Args:
        vote_event_id: str
            voteEvent's ID
        vote_logs: List[Dict[str, Any]]
            List of votes info
        batch_max: int @optional
            The max amount of votes create in ONE query
    """
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Remove all votes from voteEvent
    asyncio.run(update_vote_event(
        client=apollo_client,
        params={
            "where": {
                "id_EQ": vote_event_id
            },
            "update": {
                "votes": [{
                    "delete": [{
                        "where": {
                                "node": None
                            }
                        }]
                }]
            }
        }
    ))
    
    # Add new votes
    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        vote_logs=vote_logs,
        batch_max=batch_max
    )

async def update_vote_data(
    vote_id: str,
    voter_name: str|None=None,
    voter_party: str|None=None,
    option: str|None=None
) -> None:
    """
    Update information in a specific vote

    Args:
        vote_id (str): ID of vote's node
        voter_name (str | None): voter's name
        voter_party (str | None): voter's party
        option (str | None): vote option
    """
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Construct update param
    update_param = {}
    if voter_name:
        update_param['voter_name_SET'] = voter_name
    if voter_party:
        update_param['voter_party_SET'] = voter_party
    if option:
        update_param['option_SET'] = option
    
    # Update vote
    await update_votes(
        client=apollo_client,
        params={
            "where": {
                "id_EQ": vote_id
            },
            "update": update_param
        }
    )
    
def get_votes_in_vote_event(
    vote_event_id:str
) -> List[Dict[str, Any]]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    get_param = {
        "where": {
            "vote_events_SOME": {
                "id_EQ": vote_event_id
            }
        }
    }
    
    return asyncio.run(get_votes(
        client=apollo_client,
        fields=[
            'id',
            'vote_order',
            'badge_number',
            'voter_name',
            'voter_party',
            'option'
        ],
        params=get_param
    ))