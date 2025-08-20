from typing import List, Dict, Any
import re
import time
import requests
from bs4 import BeautifulSoup, Comment

from .party_scraper import get_parties_info


PARTY_INFO_URL = "https://hris.parliament.go.th/manage/system/user_present/form_god.php?span=show_display&s_file=..%2F..%2Fsystem%2Fuser_present%2Fform_god.php"

def clean_text(text) -> str:
    cleaned_text = text.replace("\xa0", " ")
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)
    return cleaned_text.strip()

def get_party_member(party_id: int) -> List[Dict[str, Any]]:
    
    response = requests.get(
        PARTY_INFO_URL,
        params={
            'span': 'show_display',
            's_file': '..%2F..%2Fsystem%2Fuser_present%2Fform_god.php',
            'key_index': party_id
        }
    )
    
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    member_cards = soup.find_all('div', {'class': 'card-body'})
    
    member_data = []
    for member_card in member_cards:
        
        curr_member = None
        curr_member_info = []
            
        # Replace comment element with actual element
        for comment in member_card(text=lambda text: isinstance(text, Comment)): # type: ignore
            tag = BeautifulSoup(comment, 'html.parser') # type: ignore
            if not str(comment).startswith("<"):
                tag = BeautifulSoup("<" + comment, 'html.parser') # type: ignore
            comment.replace_with(tag)
            
        # Construct data
        for element in member_card.find_all(recursive=False):
            if element.name == "h4":
                if curr_member:
                    curr_member["name"] = curr_member_info[0]
                    curr_member["member_type"] = curr_member_info[1]
                    curr_member["party_name"] = curr_member_info[2]
                    member_data.append(curr_member)
                    # print(f"Add {curr_member['name']}")
                    curr_member = None
                    curr_member_info = []
                curr_member = {
                    "member_number": re.search("(\d+)", element.text).group(1)
                }
                continue
            if element.find('img'):
                curr_member["image_url"] = element.find('img')["src"]
                continue
            if element.name == "h6": # eng name
                curr_member["name_eng"] = clean_text(element.text)
                continue
            curr_member_info.append(clean_text(element.text)) # decode \x0
        if curr_member:
            curr_member["name"] = curr_member_info[0]
            curr_member["member_type"] = curr_member_info[1]
            curr_member["party_name"] = curr_member_info[2]
            member_data.append(curr_member)
            # print(f"Add {curr_member['name']}")
    
    return member_data

def get_membership_data() -> Dict[str, Any]:
    
    party_info = get_parties_info()
    
    membership_data = {}
    
    for party in party_info:
        total = party['total_count']
        member_data = get_party_member(party['party_id'])
        if len(member_data) != total:
            print(party['party_name'], "id :", party['party_id'])
            print(f"total not match from {total} got {len(member_data)}")
            continue
        membership_data[party['party_name']] = member_data
        time.sleep(0.2)
    # print(membership_data)
    return membership_data