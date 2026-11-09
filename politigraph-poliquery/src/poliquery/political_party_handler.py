from typing import List, Dict, Any
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.organizations import get_organizations

from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=256, ttl=120))
def get_political_parties(
    start_before: str|None=None,
    start_after: str|None=None,
    end_before: str|None=None,
    end_after: str|None=None,
) -> List[dict]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    where_param = {
        "classification": {
            "eq": "POLITICAL_PARTY"
        }
    }
    
    if start_before:
        where_param["founding_date"] = {
            "lt": start_before
        }
    if end_before:
        where_param["dissolution_date"] = {
            "lt": end_before
        }
    if start_after:
        where_param["founding_date"] = {
            "gt": start_after
        }
    if end_after:
        where_param["dissolution_date"] = {
            "gt": end_after
        }
    
    result = asyncio.run(get_organizations(
        client=apollo_client,
        fields=[
            'id',
            'name',
            'other_names { name }'
        ],
        params={
            "where": where_param
        }
    ))
    
    return result