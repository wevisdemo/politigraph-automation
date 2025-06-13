import os
import time
from dotenv import load_dotenv
import pandas as pd

from poliquery import get_apollo_client, add_vote_log, update_vote_event_validate_data, replace_vote_log, get_vote_log, get_validation_data, add_vote_logs

def add_votes_to_vote_event(
    vote_event_id: str,
    votes_df: pd.DataFrame,
    time_delay:float=0.05
):
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    # Add Votes to voteEvent
    vote_logs = votes_df.to_dict('records')
    for vote in vote_logs:
        add_vote_log(
            client=apollo_client,
            vote_event_id=vote_event_id,
            vote_info=vote
        )
        time.sleep(time_delay)

def update_votes_in_vote_event(
    vote_event_id: str,
    votes_df: pd.DataFrame,
    time_delay:float=0.1
):
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    # Add Votes to voteEvent
    votes_log = votes_df.to_dict('records')
    replace_vote_log(
        client=apollo_client,
        vote_event_id=vote_event_id,
        votes=votes_log,
        time_delay=time_delay
    )
    

def update_validate_data(
    vote_event_id: str,
    validation_data: dict,
    publish_status: str
):
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    # Add validate data
    update_vote_event_validate_data(
        apollo_client,
        vote_event_id=vote_event_id,
        validation_data=validation_data,
        publish_status=publish_status
    )
    
def get_votes_from_vote_event(
    vote_event_id: str,
):
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    votes_data = get_vote_log(apollo_client, vote_event_id)
    return votes_data

def get_validation_data_from_vote_event(
    vote_event_id: str,
):
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    # Get validation data
    validation_data_data = get_validation_data(apollo_client, vote_event_id)
    
    # Remap key to Thai
    key_mapping = {
        'agree_count': 'เห็นด้วย', 
        'disagree_count': 'ไม่เห็นด้วย', 
        'abstain_count': 'งดออกเสียง', 
        'novote_count': 'ไม่ลงคะแนนเสียง',
        'publish_status': 'publish_status'
    }
    remapped_validation_data = {key_mapping[key]: value for key, value in validation_data_data.items()}
    
    return remapped_validation_data