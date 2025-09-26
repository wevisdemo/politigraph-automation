from typing import Dict, Any, List
import re
from datetime import datetime

from thai_name_normalizer import convert_thai_number_str_to_arabic

def convert_thai_date_to_universal(thai_date_str:str|None) -> str|None:
    
    if not thai_date_str:
        return None
    
    # Parse the date string in the format dd/mm/yyyy
    dt_object = datetime.strptime(thai_date_str, '%d/%m/%Y')
    
    # Check whether the year is valid
    if dt_object.year < 2500: # year if already in Gregorian year
        # TODO update this before the year 2100 or successfully achieve Open Parliament
        year_2_digit = int(str(dt_object.year)[2:])
        gregorian_year = 2000 + year_2_digit
    else:
        # Convert the Thai year to Gregorian year by subtracting 543
        gregorian_year = dt_object.year - 543

    # Create a new datetime object with the corrected year
    universal_dt_object = dt_object.replace(year=gregorian_year)

    # Format the new datetime object into the desired yyyy-mm-dd string format
    return universal_dt_object.strftime('%Y-%m-%d')

def extract_vote_num(num_text: str) -> int:
    if 'ไม่มี' in num_text:
        return 0
    all_nums = [
        int(num) for num in re.findall(r"\d+", num_text)
    ]
    return max(all_nums)

def extract_vote_count_data(
    vote_text: str,
    vote_option_index: Dict[str, List[str]]|None= {
        'agree_count': ['เห็นชอบ', 'รับหลักการ', 'เห็นด้วย'],
        'disagree_count': ['ไม่เห็นชอบ', 'ไม่รับหลักการ', 'ไม่เห็นด้วย'],
        'abstain_count': ['งดออกเสียง'],
        'novote_count': ['ไม่ลงคะแนน', 'ไม่ลงคะแนนเสียง', 'ไม่ประสงค์ลงคะแนน'],
    }
) -> Dict[str, Any]:
    
    if not vote_option_index:
        raise ValueError("Invalid vote option index!!")
    
    # Get & Normalize vote text
    vote_text = vote_text.replace("\r", "")
    # vote_text = vote_text.replace("\n", " | ")
    vote_text = re.sub(r"\s+", " ", vote_text)
    vote_text = convert_thai_number_str_to_arabic(vote_text) # convert Thai num to Arabic
    
    # Clean vote text
    vote_option_normalizer = {
        'เห็นด้วย': 'เห็นชอบ',
        'งดออกสียง': 'งดออกเสียง', # typo
        'ไม่ประสงค์ลงคะแนน': 'ไม่ลงคะแนน',
        r'วาระ.?\d{1}': '',
    }
    for pattern_str, repl_str in vote_option_normalizer.items():
        vote_text = re.sub(pattern_str, repl_str, vote_text)
    # print(vote_text)

    vote_count_data = {}
    # Split text into chunk of text-number
    splited_texts = re.split(r"(\d+\+\d+=\d+|\d+|ไม่มี)", vote_text)
    
    # Pair splited texts to get vote count data
    for key, num_text in zip(splited_texts, splited_texts[1:]):
        for option, option_texts in vote_option_index.items():
            option_pattern = "|".join(option_texts)
            if re.search(option_pattern, key) and option not in vote_count_data.keys():
                vote_count_data[option] = extract_vote_num(num_text)
    
    # If novote_count not present set to 0
    if not vote_count_data.get('novote_count', None):
        vote_count_data['novote_count'] = 0
    
    return vote_count_data