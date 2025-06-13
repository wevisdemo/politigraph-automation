from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client

def get_apollo_client(
    subscribtion_endpoint,
    token
) -> Client:
    
    transport = AIOHTTPTransport(
        url=subscribtion_endpoint, 
        headers={'x-api-key': f"{token}"}, 
    )
    
    client = Client(transport=transport, fetch_schema_from_transport=True, execute_timeout=30)
    return client

