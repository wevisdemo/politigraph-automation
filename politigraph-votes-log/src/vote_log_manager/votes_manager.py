import os
import asyncio
from pathlib import Path

import pandas as pd
from poliquery import (
    get_apollo_client,
    add_votes_to_vote_event, 
    update_vote_event_validation_data,
    get_votes_from_vote_event,
    get_political_parties,
    get_organizations,
    update_votes
)

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
        ids = [v.get('id') for v in votes_group]
        for id_chunk in [ids[i : i + 10] for i in range(0, len(ids), 10)]:
            update_param = {
                "where": {
                    "id": {
                        "in": id_chunk
                    }
                },
                "update": {
                    "voter_affiliations": [
                    {
                        "connect": [
                        {
                            "where": {
                                "node": {
                                    "classification": {
                                       "in": [
                                           "POLITICAL_PARTY", "HOUSE_OF_SENATE"
                                       ]
                                    },
                                    "id": {
                                        "eq": party_id_index.get(affi_name)
                                    }
                                }
                            }
                        }
                        ]
                    }
                    ]
                }
            }
            asyncio.run(update_votes(
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
