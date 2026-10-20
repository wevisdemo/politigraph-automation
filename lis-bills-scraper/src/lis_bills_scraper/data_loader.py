from typing import Any
import os, re
import asyncio
from pathlib import Path
import json
from .bills import Bill

from poliquery import (
    get_all_bills_info, 
    get_prime_minister_cabinet_index,
    get_representative_members_name,
    get_all_house_of_representatives
)
from thai_name_normalizer import remove_thai_name_prefix

POLITIGRAPH_DATA_DIR = Path(__file__).resolve().parent / "politograph_data"
INSTRUCTION_DIR = Path(__file__).resolve().parent / "instructions"

def refresh_bill_data(parliament_term: int) -> None:
    politigraph_bill = asyncio.run(get_all_bills_info(parliament_term))
    data_json_path = POLITIGRAPH_DATA_DIR / f"bills-{parliament_term}.json"
    with open(data_json_path, "w") as f:
        json.dump(politigraph_bill, f, indent=4, ensure_ascii=False)

def load_bill_data(parliament_term: int) -> list[dict[str, Any]]:
    
    os.makedirs(POLITIGRAPH_DATA_DIR, exist_ok=True)
    
    data_json_path = POLITIGRAPH_DATA_DIR / f"bills-{parliament_term}.json"
    
    # If no bills data loaded; query & save to file
    if not os.path.exists(data_json_path):
        with open(data_json_path, "w") as f:
            politigraph_bill = asyncio.run(get_all_bills_info(parliament_term))
            json.dump(politigraph_bill, f, indent=4, ensure_ascii=False)
            
    # Load bills data
    with open(data_json_path, "r") as f:
        return json.load(f)
    
def load_representative_data(parliament_term: int) -> list[dict[str, Any]]:
    
    os.makedirs(POLITIGRAPH_DATA_DIR, exist_ok=True)
        
    data_json_path = POLITIGRAPH_DATA_DIR / f"representatives-{parliament_term}.json"
    
    # If no bills data loaded; query & save to file
    if not os.path.exists(data_json_path):
        with open(data_json_path, "w") as f:
            representatives_data = get_representative_members_name(parliament_term)
            json.dump(representatives_data, f, indent=4, ensure_ascii=False)
            
    # Load bills data
    with open(data_json_path, "r") as f:
        return json.load(f)

def get_name_index(parliament_term: int) -> dict[str, str]:
    
    # Load data
    representatives_data = load_representative_data(parliament_term)
    
    # Convert to name-id dict
    name_index = {
        p.get('name', 'John Doe'): p.get('id', '') for p in representatives_data
    }
    
    return name_index
    
def get_cabinet_id_with_prime_minister_name(
    prime_minister_name: str
) -> str|None:
    # Clean prime minister name
    name = remove_thai_name_prefix(prime_minister_name)
    cabinet_index = asyncio.run(get_prime_minister_cabinet_index())
    return cabinet_index.get(name)

def load_parliament_info(parliament_term: int) -> dict[str, Any] | None:
    
    os.makedirs(POLITIGRAPH_DATA_DIR, exist_ok=True)
    
    house_of_rep_data = get_all_house_of_representatives()
    
    matched_term = next(
        (h for h in house_of_rep_data if h.get('term') == parliament_term),
        None
    )
            
    return matched_term
    