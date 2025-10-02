from typing import List, Dict, Any
import asyncio

from .apollo_connector import get_apollo_client
from .query_helper.organizations import get_organizations

def get_all_house_of_representatives() -> List[Dict[str, Any]]:
    
     # Initiate client
    apollo_client = get_apollo_client()
    
    
    house_of_representatives = asyncio.run(get_organizations(
        client=apollo_client,
        fields=['id', 'name', 'term'],
        params={
            "where": {
                "classification_EQ": "HOUSE_OF_REPRESENTATIVE"
            }
        }
    ))
    
    return house_of_representatives
    