from typing import List, Dict, Any
import requests
import math
import re

from bs4 import BeautifulSoup
from .lis_web_constants import LIS_ENDPOINT, BILLS_TYPE_SYSTEM_INDEX, BIll_TYPE_CLASS_INDEX, OFFSET_STEP

async def get_bill_list(parliament_term: int) -> List[Dict[str, Any]]:
    """
    Scrape bills from the given parliament term

    Args:
        parliament_term: int
            Parliament's term.

    Returns:
        A list of bill data.
    """
    
    bills_index = BILLS_TYPE_SYSTEM_INDEX
    
    data = []
    
    for bill_type, sys_id in bills_index.items():
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
                }
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
                
                # Get url & extract Doc ID
                url = bill_info[-1]
                doc_id = 0
                if re.search(r"DOC_ID\=(\d+)", url): # type: ignore
                    doc_id = int(re.search(r"DOC_ID\=(\d+)", url).group(1)) # type: ignore
                
                data.append({
                    'bill_type': bill_type,
                    'classification': BIll_TYPE_CLASS_INDEX[bill_type],
                    'year': bill_info[2],
                    'acceptance_number': bill_info[3],
                    'title': bill_info[4],
                    'proposer': bill_info[5],
                    'result': bill_info[6],
                    'lis_doc_id': doc_id,
                    'url': url,
                })
                
            # Increase offset value
            off_set += OFFSET_STEP
    
    return data
