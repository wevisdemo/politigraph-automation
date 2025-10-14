from typing import List, Dict, Any, Hashable
import re
import asyncio

import pandas as pd

from poliquery import get_all_bills_info, create_new_multiple_bills
from .bills_scraper import get_bill_list

BILL_NORMALIZE_PATTERNS = [
    (r"พ\.ศ\.\s?\.{2,4}", ""), # พ.ศ. ....
    (r"\(?ฉบับที่\s?\.{1,}\)?", ""), # ฉบับที่ ..
    (r"พ\.ศ\.\s?\d{4}", ""), # พ.ศ. xxxx
    (r"\(?ฉบับที่\s?\d+\)?", ""), # ฉบับที่ xx
]

LIS_URL_NOTE = 'ระบบสารสนเทศด้านนิติบัญญัติ'
LIS_BASE_URL = 'https://lis.parliament.go.th/index/'

def normalize_bills_title(bill_title: str) -> str:
    normalized_title = bill_title
    
    # Normalize with pattern
    for pattern, repl in BILL_NORMALIZE_PATTERNS:
        normalized_title = re.sub(pattern, repl, normalized_title)
        
    # Normalize space
    normalized_title = re.sub(r"\s+", " ", normalized_title)
    
    return normalized_title.strip()

async def scrape_new_bills(
    parliament_term: int
) -> List[Dict[Hashable, Any]]:
    
    # Scrape Bills from web
    get_bills_task = asyncio.create_task(get_bill_list(
        parliament_term=parliament_term
    ))
    
    # Query Bills from politigraph
    query_bills_task = asyncio.create_task(get_all_bills_info(
        parliament_terms=parliament_term
    ))
    
    web_bills, politigraph_bills = await asyncio.gather(get_bills_task, query_bills_task)
    
    # Extract lis_doc_id from url in politigraph data
    for bill in politigraph_bills:
        if not bill.get('links', None):
            bill['lis_doc_id'] = 0
            continue
        links = bill.get('links', [])
        for link in links:
            if link['note'] == LIS_URL_NOTE:
                bill['lis_doc_id'] = int(re.search(r"DOC_ID\=(\d+)", link['url']).group(1)) # type: ignore
    
    # Convert both data to pandas dataframe
    web_bills_df = pd.DataFrame(web_bills)
    politigraph_bills_df = pd.DataFrame(politigraph_bills)
    
    # Get new bills
    new_bills_df = pd.concat(
        objs=[web_bills_df, politigraph_bills_df],
        ignore_index=True
    ).drop_duplicates(
        subset=['classification', 'acceptance_number', 'lis_doc_id'],
        keep=False
    )
    
    # Add base url to url
    new_bills_df.loc[:, 'url'] = new_bills_df['url'].apply(
        lambda sub_url: LIS_BASE_URL + sub_url if "lis.parliament.go.th" not in sub_url else sub_url
    )
    
    # Construct data into dict
    new_bills_data = new_bills_df.to_dict('records')
    
    return new_bills_data
    
def scrape_and_create_new_bills(
    parliament_term: int
) -> List[str]:
    # Scrape a list of new bills
    new_bills = asyncio.run(scrape_new_bills(parliament_term))
    
    # Create new bills and get ID
    new_bills_id = create_new_multiple_bills(
        bill_data=new_bills,
        parliament_term=parliament_term
    )
    
    return new_bills_id
    