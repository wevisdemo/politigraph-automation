from gql import Client
import re

from .gql_querry_helper import get_organization, get_vote_event_msbis_id, add_vote_event

def get_latest_parliament_number(client: Client, default:int=25) -> int:
    param = {
        "where": {
            "classification_EQ": "HOUSE_OF_REPRESENTATIVE",
            "dissolution_date_EQ": None
        }
    }
    result = get_organization(client=client, params=param)
    organizations = result["organizations"]
    if not organizations:
        return default
    
    parliament_num = organizations[0]["term"]
    return parliament_num if parliament_num else default

def get_latest_msbis_id(client: Client, default:int=0) -> int:
    param = {
        "sort": [
            {
                "msbis_id": "DESC"
            }
        ],
        "where": {
            "msbis_id_GT": 0
        },
        "limit": 1
    }
    result = get_vote_event_msbis_id(client=client, params=param)
    if not result["voteEvents"]:
        return default
    latest_msbis_id = result["voteEvents"][0]["msbis_id"]
    return latest_msbis_id if latest_msbis_id else default

def create_vote_event(client: Client, parliament_num: int, vote_event_info: dict, include_senate: bool=False) -> str:
    """
    Creat new vote event via apollo and return vote event id for linking with vote
    """
    bill_title = vote_event_info.get("title", "")
    event_type = vote_event_info.get("classification", None)
    msbis_id = vote_event_info.get("msbis_id", None)
    start_date = vote_event_info.get("start_date", None)
    pdf_sub_url = vote_event_info.get("pdf_url", "")

    # id for house of representative
    parliament_org_name = "สภาผู้แทนราษฎร-" + str(parliament_num)
    source_url = f"https://msbis.parliament.go.th/ewtadmin/ewt/parliament_report/main_warehouse.php?m_id={msbis_id}#detail"
    base_pdf_url = "https://msbis.parliament.go.th/ewtadmin/ewt"
    pdf_url = base_pdf_url + re.sub(r"^.*?(?=\/)", "", pdf_sub_url)
    
    create_vote_param = {
        "title": bill_title, 
        "msbis_id": msbis_id, 
        "publish_status": "PUBLISHED", 
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
                "id_EQ": parliament_org_name
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
                    "classification_EQ": "HOUSE_OF_SENATE",
                    "founding_date_LTE": start_date,
                    "OR": [
                        {"dissolution_date_GTE": start_date},
                        {"dissolution_date_EQ": None},
                    ]
                }
                }
            })
        
    create_vote_param["organizations"] = {
            "connect": org_connect_params
        }

    result = add_vote_event(client, params={"input": [create_vote_param]})
    vote_event = result["createVoteEvents"]["voteEvents"][0]
    
    return vote_event["id"]
