from typing import List, Dict, Any, Tuple

import re
import os, requests
import tempfile
from bs4 import BeautifulSoup, Tag

APPOINT_COMMITEE_SECTION_TITLE = "ข้อมูลแต่งตั้งคณะกรรมาธิการสภาผู้แทนราษฎร"
COMMITEE_RESULT_SECTION_TITLE = "ข้อมูลผลการพิจารณาของคณะกรรมาธิการ"

def create_temp_cert_file():
    
    CLIENT_CERT_STRING = os.getenv('CLIENT_CERT_STRING')
    if not CLIENT_CERT_STRING:
        raise ValueError("No CLIENT_CERT_STRING")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False) as f_cert, \
        tempfile.NamedTemporaryFile(delete=False) as f_key:
        f_cert.write(CLIENT_CERT_STRING.encode("utf-8"))
        f_cert.seek(0)
        
        cert_path = f_cert.name
        return cert_path

def get_attached_doc(section: Tag) -> str|None:
    # Check if any doc is attached to this event
    a_element = None
    for td in section.find_all('td')[::-1]: # type: ignore
        if td.find('a'): # type: ignore
            a_element = td.find('a') # type: ignore
            break
    if a_element:
        doc_url = a_element['href'] # type: ignore
        return doc_url # type: ignore

def get_appoint_committee_event_doc(lis_url: str) -> List[str|None]:
    
    cert_file_path = create_temp_cert_file()
    response = requests.get(lis_url, verify=cert_file_path)
    
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    
    # Find h3 heading
    heading_element = soup.find('h3', {'class': 'heading'})
    if not heading_element:
        raise ValueError("No Bill heading!!")
    if not heading_element.parent:
        raise ValueError("No Bill heading parent")
    
    # Loop through to get all event's sections
    doc_urls: List[str|None] = [None, None]
    elements = heading_element.parent.find_all(recursive=False)
    for header, section in zip(elements, elements[1:]):
        section_title = header.get_text(strip=True)
        if section_title == APPOINT_COMMITEE_SECTION_TITLE:
            doc_url = get_attached_doc(section) # type: ignore
            doc_urls[0] = doc_url
        elif section_title == COMMITEE_RESULT_SECTION_TITLE:
            doc_url = get_attached_doc(section) # type: ignore
            doc_urls[1] = doc_url
    return doc_urls