from gql import Client

from .query_helper.persons import update_image_url
from .query_helper.organizations import update_organiztion

def update_politician_image_url(
    client: Client,
    firstname: str,
    lastname: str,
    image_url: str
) -> dict:
    params = {
        "where": {
            "firstname_EQ": firstname,
            "lastname_EQ": lastname
        },
        "update": {
            "image_SET": image_url
        }
    }
    result = update_image_url(client=client, params=params)
    return result["updatePeople"]["people"][0] if result["updatePeople"]["people"] else None
    
def update_party_logo_image_url(
    client: Client,
    party_name: str,
    image_url: str
) -> dict:
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
    return result