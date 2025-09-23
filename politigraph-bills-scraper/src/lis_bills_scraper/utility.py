from datetime import datetime

def convert_thai_date_to_universal(thai_date_str:str) -> str:
    
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

def extract_vote_count_data(
    vote_text: str,
    vote_option_index: Dict[str, str]|None= {
        'agree_count': 'เห็นชอบ',
        'disagree_count': 'ไม่เห็นชอบ',
        'abstain_count': 'งดออกเสียง',
        'novote_count': 'ไม่ลงคะแนน',
    }
) -> Dict[str, Any]:
    
    if not vote_option_index:
        raise ValueError("Invalid vote option index!!")
    
    # Get & Normalize vote text
    vote_text = vote_text.replace("\r", "")
    # vote_text = vote_text.replace("\n", " | ")
    vote_text = re.sub(r"\s+", " ", vote_text)
    vote_text = convert_thai_number_str_to_arabic(vote_text) # convert Thai num to Arabic
    # print(vote_text)

    vote_count_data = {}
    for option, option_text in vote_option_index.items():
        if option_text not in vote_text:
            vote_count_data[option] = None
        _pattern = r"^(" + option_text + r").+?(เสียง|ไม่มี)"
        match_option = re.search(_pattern, vote_text)
        if match_option:
            _txt = match_option.group(0)
            match_num = re.search(r"\d+", _txt)
            if "ไม่มี" in _txt:
                vote_count_data[option] = 0
            elif match_num:
                vote_count_data[option] = int(match_num.group(0))
            vote_text = re.sub(_pattern, "", vote_text).strip()
    # If novote_count not present set to 0
    if not vote_count_data.get('novote_count', None):
        vote_count_data['novote_count'] = 0
    
    return vote_count_data