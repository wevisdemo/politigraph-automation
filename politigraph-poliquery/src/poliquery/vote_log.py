from typing import List, Dict
import time

from gql import Client

from .query_helper.votes import get_vote, add_vote
from .query_helper.vote_events import get_vote_event_validation_data, delete_votes_in_vote_event, add_vote_event, update_vote_event
from .query_helper.persons import agg_count_people

def get_validation_data(client: Client, vote_event_id: str) -> dict:
    agg_param = {
        "where": {
            "id_EQ": vote_event_id
        }
    }
    agg_result = get_vote_event_validation_data(client=client, params=agg_param)
    matched_vote_events = agg_result["voteEvents"]
    if len(matched_vote_events) == 0:
        print(f"No VoteEvent id: {vote_event_id}")
        return None
    return matched_vote_events[0]

def count_people(client: Client, firstname: str, lastname: str=""):
    agg_param = {
        "where": {
            "firstname_EQ": firstname
        }
    }
    if lastname != "":
        agg_param["where"]["lastname_EQ"] = lastname
    agg_result = agg_count_people(client=client, params=agg_param)
    return agg_result['peopleConnection']['aggregate']['count']['nodes']

def get_vote_log(client: Client, vote_event_id: str):
    agg_param = {
        "where": {
            "vote_events_SINGLE": {
                "id_EQ": vote_event_id
            }
        }
    }
    agg_result = get_vote(client=client, params=agg_param)
    return agg_result["votes"]
    
def add_vote_log(client: Client, vote_event_id: str, vote_info: dict):
    order = str(vote_info.get("ลําดับที่", "0")) 
    badge_number = str(vote_info.get("เลขที่บัตร", "x")) 
    name = vote_info.get("ชื่อ - สกุล", "") 
    party = vote_info.get("ชื่อสังกัด", "") 
    option = vote_info.get("ผลการลงคะแนน", "x")
    
    # initiate vote param
    vote_param = {
        "vote_order": order,
        "badge_number": badge_number, 
        "voter_name": name,
        "voter_party": party,
        "option": option
    }
    
    # add vote event id to connect
    vote_param["vote_events"] = {
            "connect": [
                {
                    "where": {
                        "node": {
                            "id_EQ": vote_event_id
                        }
                    }
                }
            ]
        }
    
    # querry to count politician with matched name
    print(order, name, option)  # TODO remove this
    name_partitioned = name.partition(" ")
    firstname = name_partitioned[0]
    lastname = name_partitioned[-1]
    people_count = count_people(
        client=client,
        firstname=firstname,
        lastname=lastname
    )
    
    # TODO handle more than 1 people with this name
    if people_count > 0:  # add connection to person
        vote_param["voters"] = {
            "connect": [
                {
                    "where": {
                        "node": {
                            "firstname_EQ": firstname,
                            "lastname_EQ": lastname
                        }
                    }
                }
            ]
        }
        
    add_vote_param = {"input": [vote_param]}
    result = add_vote(client=client, params=add_vote_param)
    return result

def add_vote_logs(client: Client, vote_event_id: str, vote_logs: list):
    
    # Construct create node param
    create_vote_param = []
    for vote in vote_logs:
        # initiate vote param
        order = str(vote.get("ลําดับที่", "0")) 
        badge_number = str(vote.get("เลขที่บัตร", "x")) 
        name = vote.get("ชื่อ - สกุล", "") 
        party = vote.get("ชื่อสังกัด", "") 
        option = vote.get("ผลการลงคะแนน", "x")
        
        print(order, name, option)
        
        # initiate vote param
        vote_param = {
            "vote_order": order,
            "badge_number": badge_number, 
            "voter_name": name,
            "voter_party": party,
            "option": option
        }
        
        # Check if Person exist & add connection
        name_partitioned = name.partition(" ")
        firstname = name_partitioned[0]
        lastname = name_partitioned[-1]
        people_count = count_people(
            client=client,
            firstname=firstname,
            lastname=lastname
        )
    
        # TODO handle more than 1 people with this name
        if people_count > 0:  # add connection to person
            vote_param["voters"] = {
                "connect": [
                    {
                        "where": {
                            "node": {
                                "firstname_EQ": firstname,
                                "lastname_EQ": lastname
                            }
                        }
                    }
                ]
            }
        
        # Add to create param
        create_vote_param.append(vote_param)
        
    param = {
        "where": {
            "id_EQ": vote_event_id
        },
        "update": {
            "votes": [
                {
                    "create": create_vote_param
                }
            ]
        }
    }
    
    # Update VoteEvent with new votes
    print(f"Adding {len(create_vote_param)} votes to VoteEvent: {vote_event_id}")
    result = update_vote_event(
        client=client, 
        params=param
    )


def replace_vote_log(client:Client, vote_event_id:str, votes:List[Dict], time_delay:float=0.1):
    # Delete Votes in VoteEvent
    param = {
        "where": {
            "vote_events_SINGLE": {
                "id_EQ": vote_event_id
            }
        }
    }
    delete_votes_in_vote_event(client=client, params=param)

    for vote in votes:
        add_vote_log(
            client=client, 
            vote_event_id=vote_event_id,
            vote_info=vote
        )
        time.sleep(time_delay)
        
def update_vote_event_validate_data(
    client: Client, 
    vote_event_id: str, 
    validation_data: dict, 
    publish_status: str=None,
    ):
    
    agree_count = validation_data.get("เห็นด้วย", -1) 
    disagree_count = validation_data.get("ไม่เห็นด้วย", -1) 
    abstained_count = validation_data.get("งดออกเสียง", -1) 
    novoted_count = validation_data.get("ไม่ลงคะแนนเสียง", -1) 
    
    if publish_status not in ["ERROR", "PUBLISHED"]:
        publish_status = "ERROR"
    
    update_event_param = {
        "where": {
            "id_EQ": vote_event_id
        },
        "update": {
            "agree_count_SET": agree_count,
            "disagree_count_SET": disagree_count,
            "abstain_count_SET": abstained_count,
            "novote_count_SET": novoted_count,
        }
    }
    
    if publish_status:
        update_event_param['update']['publish_status_SET'] = publish_status
    
    result = update_vote_event(client=client, params=update_event_param)
    return result
