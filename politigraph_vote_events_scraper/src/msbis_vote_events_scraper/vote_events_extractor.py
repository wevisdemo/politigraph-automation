import time
import re
from bs4 import BeautifulSoup

from .msbis_web_scraper import scrap_meeting_ids, request_meeting_detail
from .text_helper import decode_thai_date, clean_bill_title, clean_event_type

def scrap_msbis_vote_events(
    parliament_num: int,
    latest_id: int=0,
    pdf_base_url: str='https://msbis.parliament.go.th/ewtadmin/ewt',
):
    # TODO get latest meeting id from politigraph database
    latest_id = latest_id
    
    hos_meeting_ids, joined_meeting_ids = scrap_meeting_ids(parliament_num, latest_id)
    ids_to_check = hos_meeting_ids + joined_meeting_ids  # combine both lists

    vote_events_info = [] # store file information for OCR in next step
    
    # Check meeting records
    for mid in ids_to_check:
        print(f"Checking meeting id: {mid}")
        response = request_meeting_detail(mid)
        soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
        
        bill_title = None
        if soup.find_all('strong', string="ใบประมวลผลการลงมติ"): # check ใบประมาณผลมติ
            # display_header_text(soup.find_all('strong', string="ใบประมาณผลมติ"))
            
            bill_list = soup.find('tr', {'id': "mydetail_o"}).find_all('li')
            
            # get date
            date_string = soup.find('strong').decode_contents()
            date_string = re.sub(r".*(?<=วัน).*?ที่", "", date_string)
            date_string = re.match(r".*?(?=เวลา)", date_string).group(0)
            vote_date = decode_thai_date(date_string.strip())
            
            # check & skip if not bill with event
            vote_event_type = None
            for i in range(len(bill_list)):
                
                if "ร่าง" in str(bill_list[i]) and vote_event_type is None:
                    bill_title = clean_bill_title(str(bill_list[i]))
                    full_bill_title = bill_title

                if "ร่าง" in str(bill_list[i]) and vote_event_type:
                    bill_title = clean_bill_title(str(bill_list[i]))
                    full_bill_title = bill_title
                    vote_event_type = None

                elif "วาระ" in str(bill_list[i]) and bill_title:
                    vote_event_type = clean_event_type(str(bill_list[i]))
                
                # Check if it is MP vote event
                if vote_event_type is None:  # skip when it is not MP vote event
                    continue
                
                a_element = bill_list[i].find('a')
                if a_element and re.search("ผลการลงมติ", a_element.text):
                    pdf_sub_url = a_element["href"]
                    pdf_link = pdf_base_url + re.sub(r".*?(?=/)", "", pdf_sub_url, 1)
                    
                    # check and get if contains multi proposer
                    left_over_txt = re.sub(r"ผลการลงมติ|\(|\)", "", a_element.text).strip()
                    left_over_txt = re.sub(r"-", "", left_over_txt)
                    if left_over_txt != "":
                        full_bill_title = bill_title + left_over_txt
                    
                    pdf_file_name = re.sub(r".*\/", "", pdf_link)
                    
                    vote_events_info.append({
                        "title": full_bill_title,
                        "msbis_id": mid,
                        "vote_date": vote_date,
                        "classification": vote_event_type,
                        "pdf_url": pdf_link,
                        "pdf_file_name": pdf_file_name,
                        "include_senate": True if mid in joined_meeting_ids else False,  # default to include senate
                    })
                
        time.sleep(5) # delay to prevend Max retries exceeded

    return vote_events_info