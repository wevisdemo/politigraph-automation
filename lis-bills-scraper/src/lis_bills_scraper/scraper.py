from typing import Any
import time, re
import requests
import asyncio
import math
from requests import Response
from bs4 import BeautifulSoup
from .cert_helper import create_temp_cert_file
from .event_handlers import event_scraper_dispatcher
from .utilities import convert_thai_number_str_to_arabic
from .constants import (
    LIS_ENDPOINT, 
    BILLS_TYPE_SYSTEM_INDEX, 
    BIll_TYPE_CLASS_INDEX,
    OFFSET_STEP
)
from poliquery import get_all_house_of_representatives

def get_bill_response(url: str) -> Response | None:
    _i = 0
    while _i < 5:
        try:
            # GET bills info page
            response = requests.get(url, verify=create_temp_cert_file())
            return response
        except:
            print("request fail retry in 5 seconds...")
            time.sleep(5)
            _i += 1

def scrape_bill_data(url: str) -> list[dict[str, Any]]:

    response = get_bill_response(url)
    if not response:
        return []
    
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    # Find h3 heading
    heading_element = soup.find('h3', {'class': 'heading'})
    if not heading_element:
        raise ValueError("No Bill heading!!")
    if not heading_element.parent:
        return []
    
    # Loop through to get all event's sections
    events_element: list[tuple] = []
    elements = heading_element.parent.find_all(recursive=False)
    for header, section in zip(elements, elements[1:]):
        if header.name == 'nav':  # type: ignore
            events_element.append(
                (header, section)
            )
            
    # Get data from each event
    events_data = []
    for _, (header_element, body_element) in enumerate(events_element):
        event_title = header_element.get_text(strip=True)
        
        event_handler = event_scraper_dispatcher.get(event_title, None)
        if not event_handler:
            continue
        curr_event_data = event_handler(body_element)
        
        events_data.append(curr_event_data)
    
    return events_data

def scrape_bills_list(
    parliament_term: int | None=None
) -> list[dict[str, Any]]:
    
    if parliament_term is None:
        all_houses = get_all_house_of_representatives()
        all_houses.sort(key=lambda h: h.get('term', 25), reverse=True)
        parliament_term = all_houses[0].get('term')
    
    print(f"parliament term : {parliament_term}")
    data = []
    
    cert_file_path = create_temp_cert_file()
    
    for bill_type, sys_id in BILLS_TYPE_SYSTEM_INDEX.items():
        print(bill_type, f"S_SYSTEM : {sys_id}")
        
        total_search_result = math.inf
        off_set = 0
        # Loop through each pagination with offset
        while off_set < total_search_result:
            # GET bils page
            response = requests.get(
                LIS_ENDPOINT,
                params={
                    'S_SYSTEM': sys_id,
                    'S_SAPA_NO': parliament_term,
                    'SEARCH_DATA': 'Y',
                    'offset': off_set
                },
                verify=cert_file_path
            )
            
            soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
            
            # Get total number of bill in search result
            if math.isinf(total_search_result):
                pagination_element = soup.find('div', {'id': 'dt_d_info'})
                if pagination_element:
                    pagination_text = pagination_element.text
                    numbers = re.findall(r"\d+", pagination_text)
                    total_search_result = int(numbers[-1])
                    print(f"Found {total_search_result} bills") # TODO remove
                else:
                    total_search_result = OFFSET_STEP
                
            
            data_table = soup.find('table', attrs={'class': 'table'}) # type: ignore
            if not data_table: # if no table found skip this bils type
                break
            
            bill_row_elements = data_table.find_all('tr') # type: ignore
            
            # Extract info
            for bill_row in bill_row_elements:
                bill_info_elements = bill_row.find_all('td', recursive=False) # type: ignore
                bill_info = [
                    e.find('a')['href'] if e.find('a') else e.get_text(strip=True) for e in bill_info_elements # type: ignore
                ]
                
                if not bill_info: # skip header
                    continue
                
                # Get bill's acceptance_number
                acceptance_number = convert_thai_number_str_to_arabic(str(bill_info[3]))
                
                # Get bill title
                bill_title = convert_thai_number_str_to_arabic(str(bill_info[4]))
                
                # Check if bill is a test page, then skip
                if re.search(r"ทดสอบ|ร่างหลัก|ร่างทำนองเดียวกัน", bill_title):
                    continue
                
                # Get url & extract Doc ID
                url = bill_info[-1]
                doc_id = 0
                if re.search(r"DOC_ID\=(\d+)", url): # type: ignore
                    doc_id = int(re.search(r"DOC_ID\=(\d+)", url).group(1)) # type: ignore
                
                data.append({
                    'bill_type': bill_type,
                    'classification': BIll_TYPE_CLASS_INDEX[bill_type],
                    'year': bill_info[2],
                    'acceptance_number': acceptance_number,
                    'title': bill_title,
                    'proposer': bill_info[5],
                    'status_text': bill_info[6],
                    'lis_id': doc_id,
                    'url': "/".join(LIS_ENDPOINT.split('/')[:-1]) + '/' + str(url),
                })
                
            # Increase offset value
            off_set += OFFSET_STEP
            
    return data