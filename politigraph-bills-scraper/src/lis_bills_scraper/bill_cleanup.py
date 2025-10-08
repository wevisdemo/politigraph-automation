import asyncio

from poliquery import add_retract_event
from .bills_scraper import get_bill_list

def cleanup_bill(parliament_term: int) -> None:
    
    # Scrape bills from lis website
    lis_bill_list = asyncio.run(get_bill_list(
        parliament_term=parliament_term
    ))
    
    ############## Update bills with "ขอถอน" ##############
    # Filter retracted bills
    retracted_bill = [
        bill for bill in lis_bill_list if bill.get('result', '') == 'ขอถอน'
    ]
    
    for bill in retracted_bill:
        acceptance_number = bill.get("acceptance_number", "")
        lis_id = bill.get("lis_doc_id", 0)
        classification = bill.get("classification", "")
        add_retract_event(
            acceptance_number=acceptance_number,
            lis_id=lis_id,
            classification=classification
        )
        
    ########################################################