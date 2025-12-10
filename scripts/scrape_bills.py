# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "thai_name_normalizer", "poliquery", "msbis-vote-events-scraper",
#     "lis_bills_scraper", "tqdm"
# ]
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# msbis-vote-events-scraper = { path = "../politigraph_vote_events_scraper", editable = true }
# lis_bills_scraper = { path = "../politigraph-bills-scraper", editable = true }
# thai_name_normalizer = { path = "../politigraph-name-normalizer", editable = true }
# ///

from lis_bills_scraper import update_bills_data
from poliquery import get_all_house_of_representatives

def format_number_list(numbers):
    # Empty list, return ""
    if not numbers:
        return ""
    
    # Convert all integers to strings
    strings = [str(n) for n in numbers]
    
    # Handle single item
    if len(strings) == 1:
        return strings[0]
    
    # Join all items except the last with ", " and add the last item with " and "
    return ", ".join(strings[:-1]) + " and " + strings[-1]

def main() -> None:
    # Get all House of Representatives
    hor = get_all_house_of_representatives()
    terms = [
        h['term'] for h in hor
    ]
    
    # Scrape bill & billEvent for each term
    print(f"\nScrape Bill for House of Representatives {format_number_list(terms)}th term...\n")
    update_bills_data(terms)

if __name__ == "__main__":
    main()