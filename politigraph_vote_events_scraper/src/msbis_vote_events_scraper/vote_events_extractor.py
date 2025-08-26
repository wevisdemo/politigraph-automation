import time
import re
from bs4 import BeautifulSoup

from .msbis_web_scraper import scrap_meeting_ids, request_meeting_detail
from .text_helper import extract_date_string, decode_thai_date, clean_bill_title, clean_event_type

def scrap_msbis_vote_events(
    parliament_num: int,
    latest_id: int=0,
    start_year: int|None=None,
    stop_year: int|None=None,
    pdf_base_url: str='https://msbis.parliament.go.th/ewtadmin/ewt',
):
    
    hos_meeting_ids, joined_meeting_ids = scrap_meeting_ids(
        parliament_num, 
        latest_id,
        start_year=start_year,
        stop_year=stop_year
    )
    ids_to_check = hos_meeting_ids + joined_meeting_ids  # combine both lists
    ids_to_check.sort()

    vote_events_info = [] # store file information for OCR in next step
    
    # Check meeting records
    for mid in ids_to_check:
        new_vote_events = extract_vote_event(msbis_id=mid)
        for event in new_vote_events:
            # If it is a joined meeting, set include senate to True
            if mid in joined_meeting_ids:
                event["include_senate"] = True
            vote_events_info.append(event)
        time.sleep(5) # delay to prevent Max retries exceeded
        
    # Clean & Normalize data
    for event in vote_events_info:
        # Normalize pdf urls
        if event["pdf_url"] and not re.search("msbis.parliament.go.th", event["pdf_url"]):
            # If the pdf url is not full url, add base url
            event["pdf_url"] = re.sub(r"^\.\.", pdf_base_url, event["pdf_url"])
            
        # Add classification to title
        if not re.search(event['event_type'], event['title']):
            event['title'] += " " + event['event_type']
        
    return vote_events_info

def extract_vote_event(msbis_id:int) -> list:
    response = request_meeting_detail(msbis_id)
    print(f"Checking meeting id: {msbis_id}\n{response}")
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    if soup.find_all('strong', string="ใบประมวลผลการลงมติ"): # check ใบประมาณผลมติ
        print(f"Checking meeting id: {msbis_id} ใบประมวลผลการลงมติ\n")
        
        # get date
        raw_date_string = soup.find('strong').decode_contents() # type: ignore
        date_string = extract_date_string(raw_date_string)
        vote_date = decode_thai_date(date_string.strip())
        
        bill_list = soup.find('tr', {'id': "mydetail_o"}).find_all('li') # type: ignore
        
        return extract_vote_event_data(bill_list, msbis_id=msbis_id, date=vote_date)
    
    return []  # Return empty list if no vote event found


def extract_vote_event_data(
    bill_list:list, 
    msbis_id:int=0,
    date=None,
) -> list:
    
    # Group <li> into pair of topic and pdf link
    li_groups = []
    curr_group = []
    bill_list.reverse()  # Reverse the list to process from the end
    for btm_li, top_li in zip(bill_list, bill_list[1:]):
        if btm_li.find('b'):
            curr_group.append(btm_li)
        if is_element_vote_log(top_li):
            li_groups.append(curr_group)
            curr_group = []
            continue
        if is_element_vote_log(btm_li):
            curr_group.append(btm_li)
    if curr_group:  # Add the last group if it exists
        curr_group.append(bill_list[-1])
        li_groups.append(curr_group)  
            
    # Construct vote event data from the grouped <li>
    vote_events = []
    for group in reversed(li_groups):
        if len(group) < 2:
            continue
        
        # PDF link
        pdf_link = None
        url_note = None
        for li in group:
            if is_element_vote_log(li):
                pdf_link = li.find('a')["href"]
                url_note = li.find('a').text.strip()
        
        topic_list = []
        for li in reversed(group):
            if li.find('b'):
                topic_list.extend([
                    _.text.strip() for _ in li.find_all('b') if _.text.strip() != ""
                ])
        topic_list += [''] * (3 - len(topic_list))  # Ensure there are 3 topics
        title = topic_list[0]
        classification = topic_list[1]
        note = topic_list[2] 
        
        vote_events.append({
            "title": title,
            "msbis_id": msbis_id,
            "vote_date": date,
            "event_type": classification,
            "note": note,
            "pdf_url": pdf_link,
            "pdf_file_name": pdf_link.split("/")[-1] if pdf_link else None,
            "url_note": url_note,
            "include_senate": False,  # Default to False, can be updated later
        })
        
    # Clean & correct vote event data
    classification_patttern = [
        "วาระ",
        "มาตรา",
        "ข้อสังเกต",
        "การใช้ร่าง.*เป็นหลักในการพิจารณา",
        r"ข้อ \d+",
        "บัญชี",
        r"หมวด \d+",
        "คำปรารภ"
    ]
    for index, event in enumerate(vote_events):
        if re.search(
            r"^(\-\s)?(" + "|".join(classification_patttern) + ")", 
            event["title"].strip()
        ):
            # If title starts with classification, move it to classification
            event["note"] = event["event_type"]
            event["event_type"] = event["title"]
            # Pull previous title as title
            event["title"] = vote_events[index - 1]["title"] if index > 0 else None
        
        # Add classification & Clean title if voteEvent is a bill
        classification = clean_event_type(event["event_type"])
        if classification:
            event['title'] = clean_bill_title(event['title'])
            event["classification"] = classification
        else:
            event["classification"] = "ETC"  
                      
    return vote_events

def is_element_vote_log(element) -> bool:
    """
    Check if the element contain a vote log pdf link.
    """
    if element.find('a'):
        if re.search("ผลการลงมติ", element.text):
            return True
        if re.search("เห็นด้วยกับกรรมาธิการเสียงข้างมาก", element.text)\
            and not re.search("ตรวจสอบองค์ประชุม", element.text):
            return True
    return False
