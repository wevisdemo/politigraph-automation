import re
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.persons import get_persons

def get_politician_prefixes():
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
    
    return set([p['prefix'] for p in people_result])