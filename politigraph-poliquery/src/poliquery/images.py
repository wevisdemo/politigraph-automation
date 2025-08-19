from gql import Client
import warnings

from .apollo_connector import get_apollo_client
from .query_helper.persons import update_person
from .query_helper.organizations import update_organiztion

def update_politician_image_url(
    client: Client,
    firstname: str,
    lastname: str,
    image_url: str,
) -> None:
    """
    Update politician image url

    Args:
        client: gql.Client @deprecated
            The GQL client with a fetched schema.
        firstname: str
            Person's firstname
        lastname: str
            Person's lastname
        image_url: str
            url of the image file
    """
    
    if not client:
        client = get_apollo_client()
    
    params = {
        "where": {
            "firstname_EQ": firstname,
            "lastname_EQ": lastname
        },
        "update": {
            "image_SET": image_url
        }
    }
    result = update_person(client=client, params=params)
    
def update_party_logo_image_url(
    client: Client,
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
    
    client = get_apollo_client()
    
    params = {
        "where": {
            "classification_EQ": "POLITICAL_PARTY",
            "name_EQ": party_name
        },
        "update": {
            "image_SET": image_url
        }
    }
    result = update_organiztion(client=client, params=params)