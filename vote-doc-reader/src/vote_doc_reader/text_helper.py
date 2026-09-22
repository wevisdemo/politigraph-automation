import re
from .constants import THAI_MONTHS

def extract_max_number(raw_text: str) -> str:
    numbers = [int(n) for n in re.findall(r"\d+", raw_text)]
    return max(numbers + [0]) # type: ignore

def extract_date_from_text(raw_text: str) -> str:
    
    date = 1
    month = 1
    year = 2000
    
    # Check date
    date_match = re.search(r"วัน.+?(\d+)", raw_text)
    if date_match:
        date = int(date_match.group(1))
        
    # Check month
    month_match_pttrn = "|".join(THAI_MONTHS)
    month_match = re.search(r"(" + month_match_pttrn + r")", raw_text)
    if month_match:
        month = THAI_MONTHS.index(month_match.group(1)) + 1
    
    # Check year
    year_match = re.search(r"พ\.ศ\.\s?(25\d{2})", raw_text)
    if year_match:
        year = int(year_match.group(1)) - 543
        
    return f"{year}-{str(month).zfill(2)}-{str(date).zfill(2)}"
