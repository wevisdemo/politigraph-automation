from typing import List, Dict, Any, Hashable
import asyncio
import re

from .apollo_connector import get_apollo_client
from .query_helper.memberships import get_memberships, update_membership, create_membership
from .query_helper.posts import get_posts, create_post
from .query_helper.organizations import get_organizations

from cachetools import cached, TTLCache


def get_person_current_memberships(
    person_id: str
) -> List[Dict[str, Any]]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    param = {
        "where": {
            "end_date_EQ": None,
            "members_SOME": {
            "Person": {
                "id_EQ": person_id
            }
            },
        }
    }
    
    memberships = asyncio.run(get_memberships(
        client=apollo_client,
        fields=[
            'id',
            'label',
            'start_date',
            'end_date',
            'posts { \nid \nrole \nlabel }'
        ],
        params=param
    ))
    
    return memberships

def update_membership_info(
    membership_id: str,
    update_param: Dict[str, Any]
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    params = {
        "where": {
            "id_EQ": membership_id
        },
        "update": update_param
    }
    
    asyncio.run(update_membership(
        client=apollo_client,
        params=params
    ))

@cached(cache=TTLCache(maxsize=256, ttl=30))    
def get_party_posts(party_name: str) -> List[Dict[str, Any]]:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Find post in org
    return asyncio.run(get_posts(
        client=apollo_client,
        fields=[
            'id', 'role', 'start_date'
        ],
        params={
            "where": {
                "organizations_SINGLE": {
                    "id_EQ": "พรรค" + party_name
                }
            }
        }
    ))

async def create_new_post_in_party(
    client, 
    party_name: str,
    post_role: str 
) -> None:
    # Create param
    create_post_param = {
        "input": [
            {
                "start_date": None,
                "role": post_role,
                "organizations": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "classification_EQ": "POLITICAL_PARTY",
                                    "id_EQ": "พรรค" + party_name
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    await create_post(
        client=client,
        params=create_post_param
    )

def create_new_political_party_membership(
    person_id: str,
    party_name: str,
    post_role: str,
    membership_start_date: str
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Get post in party
    party_posts = get_party_posts(party_name=party_name)
    # print(party_posts)
    post_role_list = [p['role'] for p in party_posts]
    
    if post_role not in post_role_list: # this post don't exist in this org
        # Create new post in org
        asyncio.run(create_new_post_in_party(
            client=apollo_client,
            party_name=party_name,
            post_role=post_role
        ))
        
    # Connect person to new post
    # Create new membership
    create_membership_param = {
        "input": [
            {
                "start_date": membership_start_date,
                "label": None,
                "members": {
                    "Person": {
                        "connect": [
                            {
                                "where": {
                                    "node": {
                                        "id_EQ": person_id
                                    }
                                }
                            }
                        ]
                    }
                },
                "posts": {
                    "connect": [
                    {
                        "where": {
                            "node": {
                                "role_EQ": post_role,
                                "organizations_SINGLE": {
                                    "id_EQ": "พรรค" + party_name
                                }
                            }
                        }
                    }
                    ]
                }
            }
        ]
    }
    asyncio.run(create_membership(
        client=apollo_client,
        params=create_membership_param
    ))
        
async def create_new_post_in_cabinet(
    cabinet_term: int,
    role: str,
    start_date: str
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    # Create param
    create_post_param = {
        "input": [
            {
                "role": role,
                "start_date": start_date,
                "organizations": {
                    "connect": [
                        {
                            "where": {
                                "node": {
                                    "classification_EQ": "CABINET",
                                    "id_EQ": f"คณะรัฐมนตรี-{cabinet_term}"
                                }
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    await create_post(
        client=apollo_client,
        params=create_post_param
    )

def create_new_cabinet_membership(
    person_id: str,
    cabinet_term: int,
    post_role: str,
    membership_start_date: str
) -> None:
    
    # Initiate client
    apollo_client = get_apollo_client()
    
    create_membership_param = {
        "input": [
            {
                "start_date": membership_start_date,
                "label": None,
                "members": {
                    "Person": {
                        "connect": [
                            {
                                "where": {
                                    "node": {
                                        "id_EQ": person_id
                                    }
                                }
                            }
                        ]
                    }
                },
                "posts": {
                    "connect": [
                    {
                        "where": {
                            "node": {
                                "role_EQ": post_role,
                                "organizations_SINGLE": {
                                    "id_EQ": f"คณะรัฐมนตรี-{cabinet_term}"
                                }
                            }
                        }
                    }
                    ]
                }
            }
        ]
    }
    
    asyncio.run(create_membership(
        client=apollo_client,
        params=create_membership_param
    ))
    