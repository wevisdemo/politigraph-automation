from gql import Client
import warnings
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.persons import update_person, get_persons
from .query_helper.organizations import update_organiztion

def update_politician_image_url(
    name: str,
    image_url: str,
) -> None:
    """
    Update politician image url

    Args:
        name: str
            Person's fullname
        image_url: str
            url of the image file
    """
    
    apollo_client = get_apollo_client()
    
    # Get all person with similar firstname
    firstname = name.split(" ")[0]
    params = {
        "where": {
            "firstname": {
                    "contains": firstname
                }
            }
    }
    
    persons = asyncio.run(get_persons(
        client=apollo_client,
        fields=['id', 'name', 'firstname', 'middlename', 'lastname'],
        params=params
    ))
    
    person_id_index = {
        d['name']: d['id'] for d in persons
    }
    
    # Construct params
    params = {
        "where": {
            "id": {
                "eq": person_id_index.get(name, None)
            },
        },
        "update": {
            "image": {
                "set": image_url
            }
        }
    }
    result = asyncio.run(update_person(client=apollo_client, params=params))
    
def update_party_logo_image_url(
    party_name: str,
    image_url: str
) -> None:
    """
    Update political party image url

    Args:
        client: gql.Client @deprecated
            The GQL client with a fetched schema.
        party_name: str
            Party's name
        image_url: str
            url of the image file
    """
    
    apollo_client = get_apollo_client()
    
    params = {
        "where": {
            "classification": {
                "eq": "POLITICAL_PARTY"    
            },
            "name": {
                "eq": party_name
            }
        },
        "update": {
            "image": {
                "set": image_url
            }
        }
    }
    result = asyncio.run(update_organiztion(
        client=apollo_client, 
        params=params
    ))