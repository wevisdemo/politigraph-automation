from typing import Dict, Any, List
import re
from datetime import datetime
from rapidfuzz import distance

def convert_thai_number_str_to_arabic(thai_string: str) -> str:
    """
    Converts a string containing Thai numerals to Arabic numerals.

    This function takes a string that may contain Thai numerals (๐-๙) and
    translates them into their corresponding Arabic numeral (0-9) equivalents.
    Other characters in the string remain unchanged.

    Args:
    thai_string: The input string to be converted.

    Returns:
    A new string with all Thai numerals converted to Arabic numerals.
    """
    thai_to_arabic_map = str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789')
    return thai_string.translate(thai_to_arabic_map)

def convert_thai_date_to_universal(thai_date_str:str|None) -> str|None:
    
    if not thai_date_str:
        return None
    
    # Split the input string into day, month, and Thai year
    day, month, thai_year = thai_date_str.split('/')

    # Convert the Thai year to an integer
    universal_year = int(thai_year)
    
    # Check whether the year is valid
    if universal_year < 2500: # year if already in Gregorian year
        # TODO update this before the year 2100 or successfully achieve Open Parliament
        year_2_digit = int(str(universal_year)[2:])
        gregorian_year = 2000 + year_2_digit
    else:
        # Convert the Thai year to Gregorian year by subtracting 543
        gregorian_year = universal_year - 543

    # Create a new datetime object with the corrected year
    date_obj = datetime(gregorian_year, int(month), int(day))

    # Format the new datetime object into the desired yyyy-mm-dd string format
    return date_obj.strftime('%Y-%m-%d')

def extract_vote_num(num_text: str) -> int:
    if re.search(r"(ไม่มี|-)", num_text):
        return 0
    all_nums = [
        int(num) for num in re.findall(r"\d+", num_text)
    ]
    return max(all_nums)

def clean_vote_text(vote_text: str|None) -> str|None:
    if not vote_text:
        return
    
    vote_option_normalizer = {
        r"\s+": " ",
        r"วาระที่\s+\d{1}": "",
        r"(\d+)": r"\g<1> เสียง",
        r"(\d+\s?)เสียง\s+": r"\g<1>เสียง\n",
        r"หลักก.{1}ร": "หลักการ",
    }
    # Clean text
    for pattern_str, repl_str in vote_option_normalizer.items():
        vote_text = re.sub(pattern_str, repl_str, vote_text)
    
    return vote_text

def extract_vote_count_data(
    vote_text: str|None,
    vote_option_index: Dict[str, List[str]]|None= {
        'agree_count': ['เห็นชอบ', 'รับหลักการ', 'เห็นด้วย'],
        'disagree_count': ['ไม่เห็นชอบ', 'ไม่รับหลักการ', 'ไม่เห็นด้วย'],
        'abstain_count': ['งดออกเสียง', 'งด'],
        'novote_count': ['ไม่ลงคะแนน', 'ไม่ลงคะแนนเสียง', 'ไม่ประสงค์ลงคะแนน'],
    },
    vote_result:str|None=""
) -> Dict[str, Any]:
    
    if not vote_option_index:
        raise ValueError("Invalid vote option index!!")
    
    if not vote_text:
        return {
            'agree_count': None,
            'disagree_count': None,
            'abstain_count': None,
            'novote_count': None,
        }
    
    # Check if pass and contain only one number
    if vote_result and vote_result.strip() in ['รับหลักการ']\
        and re.search(r"^\d+$", vote_text.strip()):
            number_match = re.search(r"^\d+$", vote_text.strip())
            if number_match:
                return {
                    'agree_count': int(number_match.group(0)),
                    'disagree_count': None,
                    'abstain_count': None,
                    'novote_count': None,
                }
    
    # Get & Normalize vote text
    if not vote_text:
        return {}
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

    vote_count_data = {}
    # Split text into chunk of text-number
    splited_texts = re.split(r"(\d+\+\d+=\d+|\d+|ไม่มี|-)", vote_text)
    
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

def correct_typo(
    typo_text: str,
    correct_texts_list: List[str],
    similarity_threshold: int = 90
) -> str:
    """
    Corrects a Thai typo based on a list of correct texts using Levenshtein distance.
    """
    
    if not correct_texts_list:
        return typo_text
    
    best_match = typo_text
    least_distance = float('inf')
    for correct_text in correct_texts_list:
        # Calculate Levenshtein distance
        dist = distance.Levenshtein.distance(typo_text, correct_text)
        # If the distance is less than the threshold, consider it a match
        if dist < least_distance:
            least_distance = dist
            best_match = correct_text
            if dist <= 1:
                break
    # Calculate character distance threshold
    char_distance_threshold = max(
        round(len(typo_text.replace(" ", "").strip()) * (100 - similarity_threshold) / 100),
        2 # Ensure at least 2 character difference
    )
    # If the best match is within the similarity threshold, return it
    if least_distance <= char_distance_threshold:
        return best_match
    else:
        return typo_text
    
def get_status_from_raw(status_raw: str) -> str:
    if re.search(r"ขอถอน|ตกไป|ไม่เข้าสู่กระบวนการ", status_raw):
        return 'REJECTED'
    if re.search(r"ประกาศในราชกิจจานุเบกษา", status_raw):
        return 'ENACTED'
    return 'IN_PROGRESS'
    