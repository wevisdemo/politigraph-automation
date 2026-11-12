import asyncio
import os
from pathlib import Path

import pandas as pd
from poliquery import (
    add_votes_to_vote_event,
    get_apollo_client,
    get_organizations,
    get_political_parties,
    get_politician_name_index,
    get_votes_from_vote_event,
    update_organiztion,
    update_person,
    update_vote_event_validation_data,
)


def update_vote_voter_connections(vote_event_id: str):
    
    # Construct politician match id
    politicians = get_politician_name_index(vote_event_id=vote_event_id)
    name_index = {
        key: v['id'] for key, v in politicians.items()
    }
    # import json
    # print(json.dumps(name_index, indent=2, ensure_ascii=False))
    
    votes = get_votes_from_vote_event(vote_event_id=vote_event_id)
    
    for name, id in name_index.items():
        # Check if name is in any voter_name_raw
        match_name_votes = [
            v for v in votes if v.get('voter_name_raw') == name
        ]
        if len(match_name_votes) == 1: # connect only when match exactly 1 name
            
            vote_id = match_name_votes[0]['id']
            
            # Connect person with vote
            update_person_param = {
                "where": {
                    "id": {
                        "eq": id
                    }
                },
                "update": {
                    "votes": [
                    {
                        "connect": [
                            {
                                "where": {
                                    "node": {
                                        "id": {
                                            "eq": vote_id
                                        }
                                    }
                                }
                            }
                        ]
                    }
                    ]
                }
            }
            
            asyncio.run(update_person(
                client=get_apollo_client(),
                params=update_person_param
            ))

def update_vote_party_connections(vote_event_id: str):
    
    # Construct party match id
    political_parties = get_political_parties()
    party_id_index = {
        p.get('name'):p.get('id') for p in political_parties
    }
    
    votes = get_votes_from_vote_event(vote_event_id=vote_event_id)
    
    # Check if any senate votes
    if any(v.get('voter_affiliation_raw') == 'สมาชิกวุฒิสภา' for v in votes):
        result = asyncio.run(get_organizations(
            client=get_apollo_client(),
            fields=[
                'id',
                'name'
            ],
            params={
                "where": {
                    "classification": {
                        "eq": "HOUSE_OF_SENATE"
                    },
                    "events": {
                        "some": {
                            "id": {
                                "eq": vote_event_id
                            }
                        }
                    }
                }
            }
        ))
        # Add senate to match index
        party_id_index['สมาชิกวุฒิสภา'] = result[0].get('id')

    # Group affiliation
    affiliations = list({a['voter_affiliation_raw'] for a in votes if 'voter_affiliation_raw' in a})
    
    for affi_name in affiliations:
        votes_group = [
            v for v in votes if v.get('voter_affiliation_raw') == affi_name
        ]
        vote_ids = [v.get('id') for v in votes_group]
        update_param = {
            "where": {
                "id": {
                    "eq": party_id_index.get(affi_name)
                }
            },
            "update": {
                "member_votes": [
                    {
                        "connect": [
                        {
                            "where": {
                                "node": {
                                    "id": {
                                        "in": vote_ids
                                    }
                                }
                            }
                        }
                        ]
                    }
                ]
            }
        }
        asyncio.run(update_organiztion(
            client=get_apollo_client(),
            params=update_param
        ))
        

def add_votes(
    vote_event_id: str,
    votes: pd.DataFrame|str|Path
) -> None:

    votes_df = None
    csv_file_path = None

    # Check path
    if isinstance(votes, pd.DataFrame):
        votes_df = votes.copy()
    elif isinstance(votes, str) | isinstance(votes, Path):
        csv_file_path = votes
        if isinstance(votes, str):
            csv_file_path = Path(votes)
        assert os.path.exists(csv_file_path)
        # Load to df
        votes_df = pd.read_csv(csv_file_path)

    assert votes_df is not None
    vote_logs = votes_df.to_dict('records')
    # Add votes to voteEvent
    add_votes_to_vote_event(
        vote_event_id=vote_event_id,
        vote_logs=vote_logs[::-1], # type: ignore
        batch_max=10
    )
    
    # Update vote -> people connection
    update_vote_voter_connections(
        vote_event_id=vote_event_id,
    )
    
    # Update vote -> party connection
    update_vote_party_connections(
        vote_event_id=vote_event_id,
    )

def update_vote_counts(
    vote_event_id: str,
    vote_count_data: dict[str, int]
) -> None:

    # Contruct validation_data keys
     validation_data = {
         "เห็นด้วย": vote_count_data.get('agree_count', -1),
         "ไม่เห็นด้วย": vote_count_data.get('disagree_count', -1),
         "งดออกเสียง": vote_count_data.get('abstain_count', -1),
         "ไม่ลงคะแนนเสียง": vote_count_data.get('novote_count', -1),
     }

     update_vote_event_validation_data(
         vote_event_id=vote_event_id,
         validation_data=validation_data
     )
