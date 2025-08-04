import re
from datetime import date

_TH_FULL_MONTHS = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
}

def thai_to_arabic_digit(thai_str):
    thai_digits = "๐๑๒๓๔๕๖๗๘๙"
    arabic_digits = "0123456789"
    translation_table = str.maketrans(thai_digits, arabic_digits)

    return thai_str.translate(translation_table)

def extract_date_string(full_string):
    
    # Handle date string
    # ครั้งที่ ๒๙ เป็นพิเศษ วันศุกร์ที่ ๔ กุมภาพันธ์ ๒๕๖๕ เวลา ๑๐.๔๖ - ๑๔.๕๑ น.
    # Include special cases like:
    # ครั้งที่ ๑๓ เป็นพิเศษ วันศุกร์ที่ ๒๐ เวลา ๐๙.๕๔ - ๐๐.๐๙ นาฬิกา ของวันเสาร์ที่ ๒๑ สิงหาคม ๒๕๖๔
    date_string = re.sub(r"^(.*?)(?:วัน)", "", full_string) # Clean ครั้งที่
    date_string = re.sub(r"เวลา.*?(น\.|นาฬิกา)", "", date_string) # Clean เวลา
    
    # Get min date
    date_num = min(
        int(n) for n in re.findall(r"\d{1,2}", thai_to_arabic_digit(date_string))
    )
    # Get month name
    _pattern = "|".join(_TH_FULL_MONTHS.keys())
    if not re.search(_pattern, date_string):
        return "1 มกราคม 2566"  # default date if not found
    month_name = re.search(_pattern, date_string).group(0)
    
    # Get year
    year_num = re.search(r"\d{4}", date_string)
    
    return f"{date_num} {month_name} {year_num.group(0)}"

def decode_thai_date(date_text):
    
    # Clean text
    date_text = re.sub(r"\s+", " ", date_text)  # Normalize whitespace
    
    thai_date, thai_month, thai_year = date_text.split(" ")
    date_number = int(thai_to_arabic_digit(thai_date))
    year_number = int(thai_to_arabic_digit(thai_year))
    
    month_number = _TH_FULL_MONTHS[thai_month]
    return date(year_number-543, month_number, date_number)

def clean_bill_title(html_str) -> str:
    try:
        bill_title = re.search(r"ร่าง.*?(?=<|$)", html_str).group(0)
        bill_title = re.sub("\n", "", bill_title)
    except:
        bill_title = html_str
    return bill_title
    
def clean_event_type(
    html_str,
    event_type_pattern: dict = {
        'MP_1': r"วาระ.{,3}\s?1",
        'MP_3': r"วาระ.{,3}\s?3",
    }
) -> str:
    
    event_type = thai_to_arabic_digit(html_str)
    event_type = re.sub("\s+", " ", event_type)
    
    for event_classification, pattern in event_type_pattern.items():
        if re.search(pattern, event_type):
            return event_classification
    print(html_str)
    return None
