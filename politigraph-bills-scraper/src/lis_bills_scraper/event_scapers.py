from typing import List, Dict, Any
import re

from bs4 import BeautifulSoup, Tag

from .utility import convert_thai_date_to_universal, extract_vote_count_data
from .msbis_scraper import get_msbis_id

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
            
            # Get name & party's name
            _co_propose_text_data = row_text.split("|")
            name = _co_propose_text_data[1]
            party_name = ""
            if len(_co_propose_text_data) >= 3:
                party_name = _co_propose_text_data[2]
            
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
            "event_type": f"VOTE_EVENT_MP_{vote_session}",
        }
    
    _title_txt = f"MP_{vote_session}"
    print("".join(['=' for _ in range(20)]), _title_txt, "".join(['=' for _ in range(20)]))
    
    ### Construct info text data ###
    info_text = ""
    for row in info_table.find_all('tr', recursive=False):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"
    
    # Clean info text to get only vote date
    info_text = re.sub(r"(^.+?\|)?(.?ที่ประชุมพิจารณา(.|\n)*$)", r"\g<2>", info_text)
    
    ### Construct info data ###
    event_info = construct_info_data(info_text)
    
    # Extract vote count data
    vote_count_data = extract_vote_count_data(vote_text=event_info.get("คะแนนเสียง", ""),)
        
    # Get msbis info
    term = event_info.get("ชุดที่", None)
    issue_year = event_info.get("ปีที่", None)
    session = event_info.get("สมัย", None)
    
    issue_number = event_info.get("ครั้งที่", None)
    
    # Get msbis id
    msbis_id = get_msbis_id(
        term=term,
        issue_year=issue_year,
        session=session,
        issue_number=issue_number,
    )
        
    # Get vote result
    vote_result = event_info.get("มติ", "")
    
    # Get & Convert vote date
    raw_vote_date = event_info.get("วันที่", "")
    vote_date = convert_thai_date_to_universal(raw_vote_date)
    print("".join(['=' for _ in range(42 + len(_title_txt))]))
    
    return {
        "event_type": f"VOTE_EVENT_MP_{vote_session}",
        "msbis_id": msbis_id,
        "vote_date": vote_date,
        "vote_result": vote_result,
        "vote_count": vote_count_data
    }
    
def scrape_senates_vote_event(section_element: Tag, vote_session: int=1) -> Dict[str, Any]:
    
    # Get info table
    info_table = section_element.find('tbody')
    if not isinstance(info_table, Tag):
        return {
            "event_type": f"VOTE_EVENT_SENATE_{vote_session}",
        }
        
    _title_txt = f"SENATE_{vote_session}"
    print("".join(['=' for _ in range(20)]), _title_txt, "".join(['=' for _ in range(20)]))
        
    ### Construct info text data ###
    info_text = ""
    for row in info_table.find_all('tr', recursive=False):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"
    
    # Clean info text to get only vote date
    info_text = re.sub(r"(^.+?\|)?(.?ที่ประชุมพิจารณา(.|\n)*$)", r"\g<2>", info_text)
    
    ### Construct info data ###
    event_info = construct_info_data(info_text)
    
    # Clean vote text before parse to extract with function
    vote_count_data = {}
    vote_option_normalizer = {
        r"\s+": " ",
        r"วาระที่\s+\d{1}": "",
        r"(\d+)": r"\g<1> เสียง",
        r"(\d+\s?)เสียง\s+": r"\g<1>เสียง\n"
    }
    vote_text = event_info.get("คะแนนเสียง", None)
    if vote_text:
        # Clean text
        for pattern_str, repl_str in vote_option_normalizer.items():
            vote_text = re.sub(pattern_str, repl_str, vote_text)
        print(vote_text)
        
        # Extract vote count data
        vote_count_data = extract_vote_count_data(
            vote_text=vote_text,
            # vote_option_index=vote_option_index
        )
    
    # Get vote result
    result_titles = [
        'มติ', 'การพิจารณาของวุฒิสภา'
    ]
    vote_result = None
    for _title in result_titles:
        vote_result = event_info.get(_title, "")
        if vote_result:
            break
    
    # Get & Convert vote date
    raw_vote_date = event_info.get("วันที่", None)
    vote_date = None
    if raw_vote_date:
        vote_date = convert_thai_date_to_universal(raw_vote_date)
    
    result_event_data = {
        "event_type": f"VOTE_EVENT_SENATE_{vote_session}",
        "vote_date": vote_date,
        "vote_result": vote_result,
        "vote_count": vote_count_data
    }
    
    import json
    print(json.dumps(
        result_event_data,
        indent=2,
        ensure_ascii=False
    ))
    
    print("".join(['=' for _ in range(42 + len(_title_txt))]))
    
    return result_event_data

def scrape_royal_assent(section_element: Tag) -> Dict[str, Any]:
    # Get info table
    info_table = section_element.find('tbody')
    if not isinstance(info_table, Tag):
        return {}
    
    _title_txt = f"ROYAL_ASSENT"
    print("".join(['=' for _ in range(20)]), _title_txt, "".join(['=' for _ in range(20)]))
    
    ### Construct info data ###
    info_text = ""
    for row in info_table.find_all('tr'):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"

    event_info = construct_info_data(info_text)
    
    # Get royal assent result
    royal_assent_result = event_info.get("พระบรมราชวินิจฉัย", None)
    
    import json
    print(json.dumps(
        event_info,
        indent=2,
        ensure_ascii=False
    ))
    print("".join(['=' for _ in range(42 + len(_title_txt))]))
    
    return {
        "event_type": "ROYAL_ASSENT",
        "result": royal_assent_result
    }
    
def scrape_enforce_event(section_element: Tag) -> Dict[str, Any]:
    # Get info table
    info_table = section_element.find('tbody')
    if not isinstance(info_table, Tag):
        return {}
    
    _title_txt = f"ENFORCE"
    print("".join(['=' for _ in range(20)]), _title_txt, "".join(['=' for _ in range(20)]))
    
    ### Construct info data ###
    info_text = ""
    for row in info_table.find_all('tr'):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"

    event_info = construct_info_data(info_text)
    
    # Get bill's final title
    final_name_titles = [
        'พระราชบัญญัติรัฐธรรมนูญ',
        'ชื่อพระราชบัญญัติงบประมาณรายจ่ายประจำปีงบประมาณ', # พรบ งบ
        'ชื่อที่ใช้เป็นกฎหมาย', # พระราชกำหนด
    ]
    final_title = None
    for _title in final_name_titles:
        final_title = event_info.get(_title, None)
        if final_title:
            break
    
    # Get enforce date
    enforce_date_string = event_info.get("วันที่", None)
    enforce_date = None
    if enforce_date_string:
        enforce_date = convert_thai_date_to_universal(enforce_date_string)
    
    result_event_data = {
        "event_type": "ENFORCE",
        "start_date": enforce_date,
        "final_title": final_title,
    }
    
    import json
    print(json.dumps(
        result_event_data,
        indent=2,
        ensure_ascii=False
    ))
    
    print("".join(['=' for _ in range(42 + len(_title_txt))]))
    
    return result_event_data

def scrape_reject_event(section_element: Tag) -> Dict[str, Any]:
    # Get info table
    info_table = section_element.find('tbody')
    if not isinstance(info_table, Tag):
        return {}
    
    _title_txt = f"REJECT"
    print("".join(['=' for _ in range(20)]), _title_txt, "".join(['=' for _ in range(20)]))
    
    ### Construct info data ###
    info_text = ""
    for row in info_table.find_all('tr'):
        row_text = row.get_text(separator="|", strip=True)
        info_text += row_text + "|"

    event_info = construct_info_data(info_text)
    
    # Get reject reason
    reject_reason = event_info.get("เหตุผล", None)
    
    result_event_data = {
        "event_type": "REJECT",
        "reject_reason": reject_reason,
    }
    
    import json
    print(json.dumps(
        result_event_data,
        indent=2,
        ensure_ascii=False
    ))
    
    print("".join(['=' for _ in range(42 + len(_title_txt))]))
    return result_event_data

def scrape_merge_event(section_element: Tag) -> Dict[str, Any]:
    # Get info table
    info_table = section_element.find('table')
    if not isinstance(info_table, Tag):
        return {}
    
    _title_txt = f"MERGED"
    print("".join(['=' for _ in range(20)]), _title_txt, "".join(['=' for _ in range(20)]))
    
    # Extract table data to dict
    merged_bills = []
    for tr_row in info_table.find('tbody').find_all('tr', recursive=False):  # type: ignore
        
        row_data = tr_row.find_all('td')  # type: ignore
        if not row_data:
            continue
        
        # Get acceptance number
        acceptance_number = row_data[1].get_text(strip=True)
        # Get lis_id
        # Check a element
        a_element = row_data[-1].find('a')  # type: ignore
        if not a_element:
            continue
        sub_url = a_element['href']  # type: ignore
        lis_id = re.search(r"DOC_ID\=(\d+)", sub_url).group(1)  # type: ignore
        
        merged_bills.append({
            'acceptance_number': acceptance_number,
            'sub_url': sub_url,
            'lis_id': int(lis_id)
        })
        
    import json
    print(json.dumps(
        merged_bills,
        indent=2,
        ensure_ascii=False
    ))
    
    result_event_data = {
        "event_type": "MERGE",
        "merged_bills": merged_bills
    }
        
    print("".join(['=' for _ in range(42 + len(_title_txt))]))
    return result_event_data

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
    'ข้อมูลการพิจารณาร่างฯ ของรัฐสภา วาระที่ 1': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=1), 
               
    # Vote MP_3
    'ข้อมูลการพิจารณาของสภาผู้แทนราษฎร วาระที่ 3': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=3),
    'ข้อมูลพิจารณาของสภาผู้แทนราษฎร วาระที่ 3': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=3),
    'ข้อมูลการพิจารณาร่างฯ ของรัฐสภา วาระที่ 3': lambda section_element:
        scrape_representatives_vote_event(section_element, vote_session=3),
    
    # Vote SENATE_1
    'ข้อมูลการพิจารณาของวุฒิสภา วาระที่ 1': lambda section_element:
        scrape_senates_vote_event(section_element, vote_session=1),
    'ข้อมูลวุฒิสภาพิจารณาและลงมติ': lambda section_element:
        scrape_senates_vote_event(section_element, vote_session=1), # พรบ งบ
    'ข้อมูลวุฒิสภาพิจารณา': lambda section_element:
        scrape_senates_vote_event(section_element, vote_session=1), # พระราชกำหนด
        
    # Vote SENATE_3
    'ข้อมูลการพิจารณาของวุฒิสภา วาระที่ 3': lambda section_element:
        scrape_senates_vote_event(section_element, vote_session=3),
        
    # Royal Assent
    'ข้อมูลผลการนำขึ้นทูลเกล้าทูลกระหม่อมถวาย': scrape_royal_assent,
    
    # Enforce
    'ข้อมูลการประกาศเป็นกฎหมาย': scrape_enforce_event,
    'ข้อมูลประกาศในราชกิจจานุเบกษา': scrape_enforce_event, # พรบ งบ
    'ข้อมูลการประกาศอนุมัติ พระราชกำหนด': scrape_enforce_event, # พระราชกำหนด
    
    # Reject
    'ข้อมูลร่างตกไป': scrape_reject_event,
    
    # Merge
    'ข้อมูลการพิจารณาร่างพระราชบัญญัติ เป็นร่างหลัก': scrape_merge_event,
}
