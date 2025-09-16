from typing import List, Dict, Any
import re

from bs4 import BeautifulSoup, Tag

from .utility import convert_thai_date_to_universal

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

event_scraper_dispatcher = {
    'ข้อมูลกลุ่มงานบริหารทั่วไปและสารบรรณ สำนักบริหารงานกลาง (สผ.)': scrape_bill_info,
    'ข้อมูลการตรวจสอบร่างพระราชบัญญัติ': scrape_co_proposer,
}
