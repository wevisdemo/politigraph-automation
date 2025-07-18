import os
import requests
from io import StringIO
from gql import gql
import pandas as pd
from dotenv import load_dotenv
from poliquery import get_apollo_client

def get_sheet_data(sheet_name):
    
    load_dotenv()
    
    sheet_key = os.getenv('PW_GOOGLE_SHEET_KEY')
    if sheet_key is None:
        return None
    
    # read politician data
    response = requests.get(
        f"https://docs.google.com/spreadsheets/d/{sheet_key}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    ).content.decode('utf-8')
    df = pd.read_csv(StringIO(response), sep=",")
    
    return df

def get_politician_names() -> list:
    
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    query = gql(
    """
    query Query {
        people {
            firstname
            lastname
        }
    }
    """
    )
    result = apollo_client.execute(query)  
    politician_names = [
        p['firstname'] + " " + p['lastname'] for p in result['people']
    ]
    return politician_names

def get_politician_prefixes() -> list:
    
    load_dotenv()
    
    # Load subsribtion end point & token from env
    SUBSCRIBTION_ENDPOINT = os.getenv('POLITIGRAPH_SUBSCRIBTION_ENDPOINT')
    POLITIGRAPH_TOKEN = os.getenv('POLITIGRAPH_TOKEN')
    # Get apollo client
    apollo_client = get_apollo_client(SUBSCRIBTION_ENDPOINT, POLITIGRAPH_TOKEN)
    
    query = gql(
    """
    query Query {
        people {
            prefix
        }
    }
    """
    )
    result = apollo_client.execute(query)  
    return [p['prefix'] for p in result['people']]

# TODO change to Politigraph Database
def get_politocal_party_names() -> list:
    # TODO get data from Politigraph first and fallback to Google Sheet
    
    party_df = get_sheet_data("Parties")
    if party_df is None:
        return []
    return party_df["name"].to_list()