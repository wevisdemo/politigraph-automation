import os

from dotenv import load_dotenv
from gql.transport.aiohttp import AIOHTTPTransport
from gql import Client

from cachetools import cached, TTLCache

@cached(cache=TTLCache(maxsize=1024, ttl=60))
def get_apollo_client(
    subscribtion_endpoint='',
    token=''
) -> Client:
    
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    
    if not SUBSCRIBTION_ENDPOINT:
        raise TypeError("Invalid SUBSCRIBTION_ENDPOINT!")
    
    print(f"--- Initiate Apollo Client ---") # TODO remove print
    transport = AIOHTTPTransport(
        url=SUBSCRIBTION_ENDPOINT, 
        headers={'x-api-key': f"{POLITIGRAPH_TOKEN}"}, 
    )
    
    client = Client(
        transport=transport, 
        fetch_schema_from_transport=True, 
        execute_timeout=30,
        batch_interval=1,
        batch_max=10
    )
    return client

