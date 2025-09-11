from typing import List, Dict, Any
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.persons import get_persons

from cachetools import cached, TTLCache

def get_politician_prefixes() -> List[str]:
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get latest parliament term
    param = {
        "where": {
            "memberships_SOME": {
            "posts_SOME": {
                "organizations_SOME": {
                "parents_SOME": {
                    "classification_EQ": "PARLIAMENT"
                }
                }
            }
            }
        }
    }
    
    people_result = asyncio.run(get_persons(
        client=apollo_client,
        fields=['prefix'],
        params=param
    ))
    
    return list(set([p['prefix'] for p in people_result]))

@cached(cache=TTLCache(maxsize=1024, ttl=300))
def get_people_in_party(party_name:str) -> List[Dict[str, Any]]:
    # Initiate client
    apollo_client = get_apollo_client()
    
    param = {
        "where": {
            "memberships_SOME": {
            "posts_SOME": {
                "organizations_SOME": {
                "classification_EQ": "POLITICAL_PARTY",
                "name_EQ": party_name
                }
            }
            }
        }
    }
    
    field = [
        'id', 'name', 'prefix', 'firstname', 'middlename', 'lastname',
        'memberships {\nlabel\nstart_date\nend_date}',
    ]
    
    people_result = asyncio.run(get_persons(
        client=apollo_client,
        fields=field,
        params=param
    ))
    
    return people_result