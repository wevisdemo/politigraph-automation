from typing import List, Dict, Any

import re
import requests, time
from bs4 import BeautifulSoup, Tag

APPOINT_COMMITEE_SECTION_TITLE = "ข้อมูลแต่งตั้งคณะกรรมาธิการสภาผู้แทนราษฎร"

def get_appoint_committee_event_doc(lis_url: str) -> str|None:
    response = requests.get(lis_url)
    
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    
    # Find h3 heading
    heading_element = soup.find('h3', {'class': 'heading'})
    if not heading_element:
        raise ValueError("No Bill heading!!")
    if not heading_element.parent:
        raise ValueError("No Bill heading parent")
    
    # Loop through to get all event's sections
    section_element = None
    elements = heading_element.parent.find_all(recursive=False)
    for header, section in zip(elements, elements[1:]):
        section_title = header.get_text(strip=True)
        if section_title == APPOINT_COMMITEE_SECTION_TITLE:
            section_element = section 
            break
        
    if not section_element:
        print("No appoint committee event ...")
        return
    
    # Check if any doc is attached to this event
    a_element = None
    for td in section_element.find_all('td')[::-1]: # type: ignore
        if td.find('a'): # type: ignore
            a_element = td.find('a') # type: ignore
            break
    if a_element:
        print(f"Found main bill at : {lis_url}")
        doc_url = a_element['href'] # type: ignore
        return doc_url # type: ignore

    return