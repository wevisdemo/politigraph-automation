from typing import List, Dict, Any
import re

from bs4 import BeautifulSoup, Tag

from .utility import convert_thai_date_to_universal
from .msbis_scraper import get_msbis_id
from thai_name_normalizer import convert_thai_number_str_to_arabic

def construct_info_data(info_text: str) -> Dict[str, Any]:
    event_info = {}
    for info_a, info_b in zip(info_text.split("|"), info_text.split("|")[1:]):
        if ":" in info_a:
            info_key = re.sub(r":|\s+", "", info_a).strip()
            if ":" not in info_b: # matched info pair
                event_info[info_key] = info_b
                continue
            event_info[info_key] = None
            continue
        if ":" not in info_b:
            _new_data = event_info[info_key] + " " + info_b
            event_info[info_key] = _new_data.strip()
    return event_info

def scrape_bill_info(section_element: Tag) -> Dict[str, Any]:
    
    # Get info table
    info_table = section_element.find('table')
    if not isinstance(info_table, Tag):
        return {}
    
    ### Construct info data ###
    info_text = ""
    for row in info_table.find_all('tr'):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"

    event_info = construct_info_data(info_text)
            
    # Get parliament term
    parliament_term = int(event_info.get("ชุดที่", "0"))
    
    # Get proposer
    proposer = event_info.get("เสนอโดย", "")
    proposer = re.sub(r"สมาชิกสภาผู้แทนราษฎร|\s+", " ", proposer).strip()
    
    # Get prime minister
    prime_minister = event_info.get("นายกรัฐมนตรี", None)
    
    # Get propose date string
    raw_date_string = event_info.get("ลงวันที่") or event_info.get("วันที่รับ")

    # Convert the date if it was found, otherwise assign None
    proposed_date = convert_thai_date_to_universal(raw_date_string) if raw_date_string else None
    
    return {
        "parliament_term": parliament_term,
        "event_type": "GENERAL_INFO",
        "proposer": proposer,
        "prime_minister": prime_minister,
        "proposal_date": proposed_date
    }
    
def scrape_co_proposer(section_element: Tag) -> Dict[str, Any]:
    
    # Get info table
    co_proposer_table = section_element.find('table')
    
    co_proposer_list = []
    if isinstance(co_proposer_table, Tag):
        
        for co_proposer in co_proposer_table.find_all('tr'):
            row_text = co_proposer.get_text(separator="|", strip=True)
            
            if not re.search(r"^\d+", row_text) or re.search(r"^1", row_text): # if it is header row or first name
                continue
            
            _, name, party_name, *_ = row_text.split("|")
            
            co_proposer_list.append({
                'name': name,
                'party_name': party_name
            })
    
    return {
        'event_type': "CO_PROPOSER",
        'co_proposer': co_proposer_list
    }
    
def scrape_representatives_vote_event(section_element: Tag, vote_session: int=1) -> Dict[str, Any]:
    
    # Get info table
    info_table = section_element.find('tbody')
    if not isinstance(info_table, Tag):
        return {
            "event_type": "VOTE_EVENT_MP_1",
        }
    
    print(f"{''.join(['=' for _ in range(20)])} MP_{vote_session} {''.join(['=' for _ in range(20)])}")
    
    ### Construct info text data ###
    info_text = ""
    for row in info_table.find_all('tr', recursive=False):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"
    
    # Clean info text to get only vote date
    info_text = re.sub(r"(^.+?\|)?(.?ที่ประชุมพิจารณา(.|\n)*$)", r"\g<2>", info_text)
    
    ### Construct info data ###
    event_info = construct_info_data(info_text)
    
    # Construct vote data
    vote_session_options_index = {
        1: {
            'agree_count': 'รับหลักการ',
            'disagree_count': 'ไม่รับหลักการ',
            'abstain_count': 'งดออกเสียง',
            'novote_count': 'ไม่ลงคะแนน',
        },
        3: {
            'agree_count': 'เห็นชอบ',
            'disagree_count': 'ไม่เห็นชอบ',
            'abstain_count': 'งดออกเสียง',
            'novote_count': 'ไม่ลงคะแนน',
        },
    }
    vote_option_index = vote_session_options_index.get(vote_session, {})
    
    # Get & Normalize vote text
    vote_text = event_info.get("คะแนนเสียง", "").replace("\r", "")
    # vote_text = vote_text.replace("\n", " | ")
    vote_text = re.sub(r"\s+", " ", vote_text)
    vote_text = convert_thai_number_str_to_arabic(vote_text) # convert Thai num to Arabic
    print(vote_text)

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
        
    # Get msbis info
    term = event_info.get("ชุดที่", None)
    issue_year = event_info.get("ปีที่", None)
    session = event_info.get("สมัย", None)
    
    issue_number = event_info.get("ครั้งที่", None)
    vote_date = event_info.get("วันที่", None)
    
    # Get msbis id
    msbis_id = get_msbis_id(
        term=term,
        issue_year=issue_year,
        session=session,
        issue_number=issue_number,
    )
        
    # Get vote result
    vote_result = event_info.get("มติ", "")
    
    print(f"{''.join(['=' for _ in range(50)])}")
    
    return {
        "event_type": f"VOTE_EVENT_MP_{vote_session}",
        "msbis_id": msbis_id,
        "vote_date": vote_date,
        "vote_result": vote_result,
        "vote_count": vote_count_data
    }
    

event_scraper_dispatcher = {
    # General bill's info
    'ข้อมูลกลุ่มงานบริหารทั่วไปและสารบรรณ สำนักบริหารงานกลาง (สผ.)': scrape_bill_info,
    # Co-proposer info
    'ข้อมูลการตรวจสอบร่างพระราชบัญญัติ': scrape_co_proposer,
    # Vote MP_1
    'ข้อมูลการพิจารณาของสภาผู้แทนราษฎร วาระที่ 1': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=1),
    'ข้อมูลพิจารณาของสภาผู้แทนราษฎร วาระที่ 1': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=1),
    # Vote MP_3
    'ข้อมูลการพิจารณาของสภาผู้แทนราษฎร วาระที่ 3': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=3),
    'ข้อมูลพิจารณาของสภาผู้แทนราษฎร วาระที่ 3': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=3),
}
