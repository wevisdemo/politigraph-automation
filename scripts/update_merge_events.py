# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "thai_name_normalizer", "poliquery", "merge_bill_updater"
# ]
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# thai_name_normalizer = { path = "../politigraph-name-normalizer", editable = true }
# merge_bill_updater = { path = "../politigraph-merge-bill-detector", editable = true }
# ///

from dotenv import load_dotenv
import os
from merge_bill_updater import check_and_update_merge_bills

def main() -> None:
    check_and_update_merge_bills()

if __name__ == "__main__":
    main()