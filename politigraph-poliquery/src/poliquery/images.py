from gql import Client

from .query_helper.persons import update_image_url
def update_politician_image_url(
    client: Client,
    firstname: str,
    lastname: str,
    image_link: str
) -> dict:
    params = {
        "where": {
            "firstname_EQ": firstname,
            "lastname_EQ": lastname
        },
        "update": {
            "image_SET": image_link
        }
    }
    result = update_image_url(client=client, params=params)
    return result["updatePeople"]["people"][0] if result["updatePeople"]["people"] else None
    