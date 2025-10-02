# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "thai_name_normalizer", "poliquery", "msbis-vote-events-scraper",
#     "lis_bills_scraper"
# ]
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# msbis-vote-events-scraper = { path = "../politigraph_vote_events_scraper", editable = true }
# lis_bills_scraper = { path = "../politigraph-bills-scraper", editable = true }
# thai_name_normalizer = { path = "../politigraph-name-normalizer", editable = true }
# ///

from lis_bills_scraper import scrape_and_create_new_bills, scrape_and_update_bill_events, cleanup_bill
from poliquery import get_all_house_of_representatives

def main() -> None:
    # Get all House of Representatives
    hor = get_all_house_of_representatives()
    terms = [
        h['term'] for h in hor
    ]
    
    # Scrape bill & billEvent for each term
    for term in terms:
        print(f"\nScrape Bill for House of Representatives {term}th term...\n")
        scrape_and_create_new_bills(term)
        scrape_and_update_bill_events(term)
        print(f"\nCleanup BillEvent for House of Representatives {term}th term...\n")
        cleanup_bill(term)

if __name__ == "__main__":
    main()