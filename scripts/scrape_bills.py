import os
from dotenv import load_dotenv
from lis_bills_scraper import Bill
from lis_bills_scraper import (
    scrape_bills_list, 
    create_new_bill, 
    update_bill_events, 
    cleanup_bill
)


def main() -> None:
    
    load_dotenv()
    
    raw_term = os.getenv('PARLIAMENT_TERM') or None
    PARLIAMENT_TERM = int(raw_term) if raw_term else None
    
    bills_data = scrape_bills_list(int(PARLIAMENT_TERM) if PARLIAMENT_TERM else None)
    
    bill_list: list[Bill] = []
    for bill_data in bills_data:
        assert bill_data.get('acceptance_number') is not None, "acceptance_number is None"
        bill_list.append(
            Bill(
                title=bill_data.get('title', ''),
                acceptance_number=bill_data.get('acceptance_number', ''),
                lis_id=bill_data.get('lis_id', 0),
                url=bill_data.get('url', ''),
                status_text=bill_data.get('status_text', ''),
                classification=bill_data.get('classification', ''),
            )
        )
    
    # Create bills
    for bill in bill_list:
        create_new_bill(bill)
        
    # Update events & cleanup
    for bill in bill_list:
        update_bill_events(bill)
        cleanup_bill(bill)

if __name__ == "__main__":
    main()