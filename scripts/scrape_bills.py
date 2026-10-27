import os
from dotenv import load_dotenv
from tqdm.auto import tqdm
from lis_bills_scraper import Bill
from lis_bills_scraper import (
    scrape_bills_list, 
    create_new_bill, 
    update_bill_events, 
    cleanup_bill
)

def is_true(value: str | None, default: bool = False) -> bool:
    """Returns True/False. Falls back to default if unset or empty (e.g. on cron runs)."""
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("true", "1", "yes")

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
        
    status_flags = {
        "IN_PROGRESS": is_true(os.getenv("SCRAPE_IN_PROGRESS"), default=True),
        "ENACTED": is_true(os.getenv("SCRAPE_ENACTED"), default=False),
        "REJECTED": is_true(os.getenv("SCRAPE_REJECTED"), default=False),
    }

    # Construct the list of selected statuses
    selected_statuses = [status for status, enabled in status_flags.items() if enabled]

    # Filter bills with selected status
    bill_list = [
        bill for bill in bill_list if bill.get_lis_status() in selected_statuses
    ]
        
    # Scrape bill events
    for bill in tqdm(bill_list):
        bill.scrape_events()
    
    # Create bills
    for bill in bill_list:
        create_new_bill(bill)
        
    # Update events & cleanup
    for bill in bill_list:
        update_bill_events(bill)
        cleanup_bill(bill)

if __name__ == "__main__":
    main()