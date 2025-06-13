import os
import requests
from io import StringIO

import pandas as pd
from dotenv import load_dotenv

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
    # TODO get data from Politigraph first and fallback to Google Sheet
    
    # clean politician names
    politician_df = get_sheet_data("Politicians")
    if politician_df is None:
        return []

    # TODO add prefix
    politician_names = politician_df.apply(lambda row: " ".join([row["firstname"], row["lastname"]]), axis=1)
    return politician_names

# TODO change to Politigraph Database
def get_politocal_party_names() -> list:
    # TODO get data from Politigraph first and fallback to Google Sheet
    
    party_df = get_sheet_data("Parties")
    if party_df is None:
        return []
    return party_df["name"].to_list()