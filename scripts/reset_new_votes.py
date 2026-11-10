import asyncio
from pathlib import Path

import pandas as pd
from poliquery import delete_votes, get_apollo_client
from vote_log_manager import add_votes
from vote_log_manager.data_cleaner import clean_votes_df

VOTE_EVENT_ID = ""

VOTES_PATH = Path("re-votes.csv")

def main() -> None:

    # Load Votes
    votes_df = pd.read_csv(VOTES_PATH)

    # Clean votes df
    votes_df = clean_votes_df(votes_df)
    
    # Delete votes
    asyncio.run(delete_votes(
        client=get_apollo_client(),
        params={
            "where": {
                "vote_events": {
                    "some": {
                        "id": {
                            "eq": VOTE_EVENT_ID
                        }
                    }
                }
            }
        }
    ))

    # Add votes
    add_votes(
        VOTE_EVENT_ID,
        votes_df
    )
    
    print(f"added new votes to :\n{VOTE_EVENT_ID}")
    
if __name__ == "__main__":
    main()
