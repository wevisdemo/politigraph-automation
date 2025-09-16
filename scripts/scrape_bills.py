# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "thai_name_normalizer", "poliquery",
#     "lis_bills_scraper"
# ]
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# lis_bills_scraper = { path = "../politigraph-bills-scraper", editable = true }
# thai_name_normalizer = { path = "../politigraph-name-normalizer", editable = true }
# ///

from lis_bills_scraper import scrape_and_create_new_bills

def main() -> None:
    print("Hello from Bills scraper")
    
    scrape_and_create_new_bills(25)

if __name__ == "__main__":
    main()