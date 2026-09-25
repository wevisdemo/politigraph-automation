from dotenv import load_dotenv
import os
from merge_bill_updater import check_and_update_merge_bills

def main() -> None:
    load_dotenv()
    
    check_and_update_merge_bills()

if __name__ == "__main__":
    main()