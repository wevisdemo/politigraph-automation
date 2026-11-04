import asyncio
import os
import re
import time
from pathlib import Path

from poliquery import create_vote_event, get_apollo_client
from vote_doc_vision import get_vote_log_object
from vote_log_manager import add_votes, clean_votes_df

# PDF folder
PDF_DIR = Path(__file__).resolve().parent.parent / "pdf"

def main() -> None:

    assert os.path.exists(PDF_DIR), "pdf folder not found!!"

    apollo_client = get_apollo_client()

    import pandas as pd
    drive_link_df = pd.read_csv("senate_doc_links.csv")
    drive_link_index = drive_link_df.set_index('File Name')['File Link'].to_dict()

    for filename in os.listdir(PDF_DIR):
        pdf_path = PDF_DIR / filename
        vote_log = get_vote_log_object(pdf_path=pdf_path, classification_type='SENATE')

        classification = vote_log.get_classification()
        print(f"classification : {classification}")
        time.sleep(2)
        if not re.search(r"SENATE\_(1|3)", classification): # type: ignore
            print("skip ...")
            continue

        print(f"title : {vote_log.get_title()}")
        print()

        vote_log.get_votes()

        # Vote count
        vote_count = vote_log.get_vote_count()

        # Create new voteEvent
        param = {
            "input": [
                {
                    "title": vote_log.get_title(),
                    "classification": vote_log.get_classification(),
                    "start_date": vote_log.get_start_date(),
                    "end_date": vote_log.get_start_date(),
                    "agree_count": vote_count.get('agree_count'),
                    "disagree_count": vote_count.get('disagree_count'),
                    "abstain_count": vote_count.get('abstain_count'),
                    "novote_count": vote_count.get('novote_count'),
                    "publish_status": "ERROR",
                    "organizations": {
                        "connect": [
                            {
                                "where": {
                                    "node": {
                                        "id": {
                                            "eq": "วุฒิสภา-13" # TODO: update method to connect this
                                        }
                                    }
                                }
                            }
                        ]
                    },
                    "links": {
                        "create": [
                            {
                                "node": {
                                    "note": "ใบประมวลผลการลงมติ",
                                    "url": drive_link_index.get(filename)
                                }
                            }
                        ]
                    }
                }
            ]
        }

        # Create new VoteEvent
        result = asyncio.run(create_vote_event(
            client=apollo_client,
            params=param
        ))

        vote_events = result['createVoteEvents']['voteEvents']
        vote_event_id = vote_events[0]['id']
        print(f"create new VoteEvent ID : {vote_event_id}")

        votes = clean_votes_df(vote_log.get_votes_df())
        votes["ชื่อสังกัด"] = "สมาชิกวุฒิสภา"

        # OCR and add votes
        add_votes(
            vote_event_id=vote_event_id,
            votes=votes
        )
        break

if __name__ == "__main__":
    main()
