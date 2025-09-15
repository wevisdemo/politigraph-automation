import re
import time
import asyncio

from hris_scraper import get_membership_data
from poliquery import get_politician_prefixes, get_people_in_party

from .name_normalizer import normalize_thai_name

def validate_representatives_memberships():
    membership_data = get_membership_data()
    
    # prefixes = get_politician_prefixes()
    def clean_prefix(name:str, prefixes:list=[]):
        return min(
            [re.sub(r"^" + prefix, "", name).strip() for prefix in prefixes],
            key=len
        )
    politician_prefixes = asyncio.run(get_politician_prefixes())
    
    _data_to_save = []
    for party_name, memberships in membership_data.items():
        _data_to_save.extend(memberships)
        print(f"----- {party_name} -----")
        
        # Clean prefix & Normalize name
        for member in memberships:
            _name = member['name']
            _name = clean_prefix(_name, politician_prefixes)
            member['name'] = normalize_thai_name(_name)
        
        # Initiate set from original List
        member_web = set([
            d['name'] for d in memberships
        ])
        
        # Get Membership from Politigraph
        people_in_party = get_people_in_party(party_name=party_name)
        member_politigraph = set([
            d['name'] for d in people_in_party
        ])
        
        print(f"Membership count from WEB : {len(memberships)}")
        print(f"Membership count from WEB to set : {len(member_web)}")
        print(f"Membership count from POLITIGRAPH : {len(member_politigraph)}")
        
        # Check which set is bigger then use as source
        print("Found on the WEBSITE but not on POLITIGRAPH")
        for name in member_web - member_politigraph:
            print(" ".join([c for c in name]))
        print()
        print("Found on the POLITIGRAPH but not on WEBSITE")
        for name in member_politigraph - member_web:
            print(" ".join([c for c in name]))
        
        print()
        print()
        time.sleep(0.2)
    