import re
from datetime import date

def thai_to_arabic_digit(thai_str):
    thai_digits = "๐๑๒๓๔๕๖๗๘๙"
    arabic_digits = "0123456789"
    translation_table = str.maketrans(thai_digits, arabic_digits)

    return thai_str.translate(translation_table)

def decode_thai_date(date_text):
    
    # Clean text
    date_text = re.sub(r"\s+", " ", date_text)  # Normalize whitespace
    
    thai_date, thai_month, thai_year = date_text.split(" ")
    date_number = int(thai_to_arabic_digit(thai_date))
    year_number = int(thai_to_arabic_digit(thai_year))
    
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
    
    month_number = _TH_FULL_MONTHS[thai_month]
    return date(year_number-543, month_number, date_number)

def clean_bill_title(html_str) -> str:
    try:
        bill_title = re.search(r"(?<=<b>).*?(?=<)", html_str).group(0)
        bill_title = re.sub("\n", "", bill_title)
    except:
        bill_title = ""
    return bill_title
    
def clean_event_type(html_str) -> str:
    
    if not re.search("วาระ", html_str):
        return ""
    event_type = thai_to_arabic_digit(re.search("วาระ.+?(?=<)", html_str).group(0))
    
    if re.search("วาระ", event_type) and re.search("1", event_type):
        return "MP_1"
    if re.search("วาระ", event_type) and re.search("3", event_type):
        return "MP_3"
    return None