from typing import List, Dict, Any
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.persons import get_persons, create_person

from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=256, ttl=120))
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
        'other_names { ... on AlternatePersonName { name } ... on AlternateName { name } }',
    ]
    
    people_result = asyncio.run(get_persons(
        client=apollo_client,
        fields=field,
        params=param
    ))
    
    return people_result

@cached(cache=TTLCache(maxsize=1024, ttl=300))
def get_representative_members_name(parliament_term:int=26) -> List[Dict[str, Any]]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    field = [
        'id', 'prefix', 'name',
        'other_names { ... on AlternatePersonName { name } ... on AlternateName { name } }',
    ]
    
    param = {
        "where": {
            "memberships_SOME": {
                "posts_SOME": {
                    "role_EQ": "สมาชิกสภาผู้แทนราษฎร",
                    "organizations_SOME": {
                        "id_EQ": f"สภาผู้แทนราษฎร-{parliament_term}"
                    }
                }
            }
        }
    }
    
    # Get every person with membership in a specific parlaiment term
    people_result = asyncio.run(get_persons(
        client=apollo_client,
        fields=field,
        params=param
    ))
    
    return people_result

def create_politician(
    prefix: str,
    firstname: str,
    lastname: str,
    middlename: str|None=None
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Construct input param
    input_param = {
        "prefix": prefix,
        "firstname": firstname,
        "lastname": lastname,
        "publish_status": "PUBLISHED"
    }
    
    # Check middlename & add to input param
    if middlename:
        input_param['middlename'] = middlename
    
    asyncio.run(create_person(
        client=apollo_client,
        params={
            "input": [input_param]
        }
    ))