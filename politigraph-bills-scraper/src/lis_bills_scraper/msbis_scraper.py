from typing import List, Dict, Any
import re

from bs4 import BeautifulSoup, Tag
from cachetools import cached, TTLCache

from msbis_vote_events_scraper import request_meeting_records, get_pagination_number
from thai_name_normalizer import convert_thai_number_str_to_arabic

def get_issue_number(text: str) -> int|None:
    match_issue_number = re.search(r"ครั้งที่\s?(\d+)", text)
    if not match_issue_number:
        return None
    return int(match_issue_number.group(1))

def get_meeting_list_from_page(
    table_element: Tag
 )-> List[Dict[str, Any]]:
    
    meeting_list = []

    if not isinstance(table_element, Tag):
        return []
    
    # Loop through all meeting list
    for meeting_element in table_element.find_all('td'):
        if "ครั้งที่" not in meeting_element.get_text(strip=True):
            continue
        # Get msbis ID
        onclick_text = meeting_element.find('a')['onclick'] # type: ignore
        match_num = re.search(r"\d+", onclick_text) # type: ignore
        if match_num: # type: ignore
            msbis_id = match_num.group(0) # type: ignore
            # Add data to main list
            meeting_text = convert_thai_number_str_to_arabic(meeting_element.get_text(strip=True))
            meeting_list.append({
                'msbis_id': msbis_id,
                'text': meeting_text,
                'issue_number': get_issue_number(meeting_text) # convert Thai num to Arabic
            })
    
    return meeting_list
        
@cached(cache=TTLCache(maxsize=64, ttl=60))
def get_msbis_meeting_list(
    term: str|None,
    issue_year: str|None,
    session: str|None,
 ) -> List[Dict[str, Any]]:
    
    meeting_list = []
    
    session_response = request_meeting_records(
        parliament_number=term,
        year=issue_year,
        session_txt=session,
        page=1
    )
    soup = BeautifulSoup(BeautifulSoup(session_response.content, "html.parser").decode(), "html.parser")
    
    # Extract first page meeting list
    meeting_list = get_meeting_list_from_page(table_element=soup)
    
    # Check pagination
    # If exist loop through page
    pagination_number = get_pagination_number(soup)
    if pagination_number > 1:
        for page_num in range(2, pagination_number + 1):
            main_session_response = request_meeting_records(
                parliament_number=term,
                year=issue_year,
                session_txt=session,
                page=page_num
            )
            soup = BeautifulSoup(BeautifulSoup(main_session_response.content, "html.parser").decode(), "html.parser")
            meeting_list.extend(get_meeting_list_from_page(table_element=soup))
    
    return meeting_list

def get_msbis_id(
    term: str|None,
    issue_year: str|None,
    session: str|None,
    issue_number: str|None,
) -> int|None:
    
    if not all([term, issue_year, session, issue_number]):
        return None
    
    # Get all meeting from this session
    meeting_list = get_msbis_meeting_list(
        term=term,
        issue_year=issue_year,
        session=session
    )
    
    match_issue_num = [
        meet for meet in meeting_list if meet['issue_number'] == int(issue_number) # type: ignore
    ]
    if len(match_issue_num) == 1: # only one exist
        return match_issue_num[0]['msbis_id']
    