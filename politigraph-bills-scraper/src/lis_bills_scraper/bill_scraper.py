from typing import List, Dict, Any
import re, math
import requests
from bs4 import BeautifulSoup
from .lis_web_constants import LIS_ENDPOINT, BILLS_TYPE_SYSTEM_INDEX, BIll_TYPE_CLASS_INDEX, OFFSET_STEP
from thai_name_normalizer import convert_thai_number_str_to_arabic

import os, tempfile

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

def scrape_bill_list(
    parliament_term: int
) -> List[Dict[str, Any]]:
    
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
            if not data_table:
                continue
            
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
                    'result': bill_info[6],
                    'lis_id': doc_id,
                    'url': "/".join(LIS_ENDPOINT.split('/')[:-1]) + '/' + str(url),
                })
                
            # Increase offset value
            off_set += OFFSET_STEP
            
    return data