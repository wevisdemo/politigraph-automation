from lis_bills_scraper import scrape_and_update_bills_data
from poliquery import get_all_house_of_representatives
from dotenv import load_dotenv
import os


def main() -> None:
    # Get all House of Representatives
    hor = get_all_house_of_representatives()
    terms = sorted([
        h['term'] for h in hor
    ], reverse=True)
    
    load_dotenv()
    if os.getenv('PARLIAMENT_PERIOD') != 'LATEST': # id not LATEST scrape previous term
        terms = terms[1:]
    
    # Scrape bill & billEvent for each term
    print(f"\nScrape Bill for House of Representatives {terms[0]}th term...\n")
    scrape_and_update_bills_data(terms[:1])

if __name__ == "__main__":
    main()