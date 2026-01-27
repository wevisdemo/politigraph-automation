import re
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.organizations import get_organizations
from .query_helper.vote_events import get_vote_events, create_vote_event

def get_latest_parliament_term(default:int=25) -> int:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get latest parliament term
    param = {
        "where": {
            "classification": {
                "eq": "HOUSE_OF_REPRESENTATIVE"
            },
            "dissolution_date": {
                "eq": None
            }
        },
        "sort": [{"founding_date": "DESC"}]
    }
    organizations = asyncio.run(get_organizations(
        client=apollo_client, 
        fields=['term'],
        params=param
    ))
    if not organizations:
        return default
    
    return organizations[0]["term"]

def get_latest_msbis_id(default:int=0) -> int:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    param = {
        "sort": [{ "msbis_id": "DESC" }],
        "where": {"msbis_id": { "gt": 0 }},
        "limit": 1
    }
    result = asyncio.run(get_vote_events(client=apollo_client, fields=['msbis_id'], params=param))
    if not result:
        return default
    latest_msbis_id = result[0]["msbis_id"]
    return latest_msbis_id if latest_msbis_id else default

def create_new_vote_event(parliament_term: int, vote_event_info: dict, include_senate: bool=False) -> str:
    """
    Creat new vote event via apollo and return vote event id for linking with vote
    """
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get all the data
    bill_title = vote_event_info.get("title", "")
    event_type = vote_event_info.get("classification", None)
    msbis_id = vote_event_info.get("msbis_id", None)
    start_date = vote_event_info.get("start_date", None)
    pdf_sub_url = vote_event_info.get("pdf_url", "")

    source_url = f"https://msbis.parliament.go.th/ewtadmin/ewt/parliament_report/main_warehouse.php?m_id={msbis_id}#detail"
    base_pdf_url = "https://msbis.parliament.go.th/ewtadmin/ewt"
    pdf_url = pdf_sub_url
    if "msbis.parliament.go.th" not in pdf_sub_url: # add base url if not included in the link
        pdf_url = base_pdf_url + re.sub(r"^.*?(?=\/)", "", pdf_sub_url)
    
    create_vote_param = {
        "title": bill_title, 
        "msbis_id": msbis_id, 
        "publish_status": "ERROR", 
        "links": {
            "create": [
                {
                    "node": {
                        "note": "ระบบฐานข้อมูลรายงานและบันทึกการประชุม", # sourceUrl
                        "url": source_url
                    }
                },
                {
                    "node": {
                        "note": "ใบประมวลผลการลงมติ", # documents
                        "url": pdf_url
                    }
                }
            ]
        }
    }
    
    # add connect to house of representative
    org_connect_params = [{
        "where": {
            "node": {
                "classification": {
                  "eq": "HOUSE_OF_REPRESENTATIVE"  
                },
                "founding_date": {
                    "lte": start_date
                },
                "OR": [
                    {"dissolution_date": {
                        "gte": start_date
                    }},
                    {"dissolution_date": {
                        "eq": None
                    }},
                ]
            }
        }
    }]
    
    if event_type:
        create_vote_param["classification"] = event_type
    if start_date:
        create_vote_param["start_date"] = start_date  # add start date
        create_vote_param["end_date"] = start_date  # add end date
        # add sanate to connect
        if include_senate:
            org_connect_params.append({
                "where": {
                    "node": {
                        "classification": {
                            "eq": "HOUSE_OF_SENATE",
                        },
                        "founding_date": {
                            "lte": start_date,
                        },
                        "OR": [
                            {"dissolution_date": {
                                "gte": start_date
                            }},
                            {"dissolution_date": {
                                "eq": None
                            }},
                        ]
                    }
                }
            })
        
    create_vote_param["organizations"] = {
            "connect": org_connect_params
        }

    result = asyncio.run(create_vote_event(apollo_client, params={"input": [create_vote_param]}))
    
    # Get newly created VoteEvent
    vote_event = result["createVoteEvents"]["voteEvents"][0]
    
    return vote_event["id"] # return id back
