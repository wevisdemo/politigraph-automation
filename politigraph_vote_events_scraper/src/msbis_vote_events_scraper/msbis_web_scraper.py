import io
import time
import urllib.parse
import re
import requests

from bs4 import BeautifulSoup

    
def request_meeting_records(
    parliament_number, 
    year, 
    session_txt,
    page=1, 
    msbis_url:str='https://msbis.parliament.go.th/ewtadmin/ewt/parliament_report/main_warehouse_list_test_sql.php'
):
    params = {
        "id": 1,
        "level": 5,
        "yearno": parliament_number,
        "year": year,
        "offset": (page - 1) * 20,  # Assuming 20 records per page
        "session_name": urllib.parse.quote_plus(session_txt, encoding='tis-620')
    }
    break_i = 0
    response = None
    while True:
        try:
            if break_i >= 5:
                break
            response = requests.get(msbis_url, params=params)
            break
        except:
            break_i += 1
            time.sleep(10)
    
    if not response:
        raise ConnectionError("Cannot get response from msbis website")
    return response

def request_joint_meeting_records(
    year, 
    session_txt, 
    level=5,
    page=1,
    msbis_url:str='https://msbis.parliament.go.th/ewtadmin/ewt/parliament_report/main_warehouse_list_test_sql.php'
):
    params = {
        "id": 3,
        "level": level,
        "yearno": 1,
        "year": year,
        "offset": (page - 1) * 20,  # Assuming 20 records per page
        "session_name": urllib.parse.quote_plus(session_txt, encoding='tis-620')
    }
    break_i = 0
    while True:
        try:
            if break_i >= 5:
                break
            response = requests.get(msbis_url, params=params)
            break
        except:
            break_i += 1
            time.sleep(10)
    return response

def request_meeting_detail(
    mid,
    meeting_detail_url = 'https://msbis.parliament.go.th/ewtadmin/ewt/parliament_report/main_warehouse_detail.php'
):
    params = {
        "mid": mid
    }

    response = requests.get(meeting_detail_url, params=params)
    return response

def get_pagination_number(soup):
    pagination = None
    for td in reversed(soup.find_all('td')): # reverse to iterate from bottom to top
        if re.search("^หน้าที่", td.text):
            pagination = td
            break
    if not pagination:
        return 1
    pages = pagination.find_all("a")
    if not pages:
        return 1
    # print(f"found {len(pages)} pages")
    return len(pages)

def scrap_votings_id(soup):
  votings_ids = []

  for td in soup.find_all("td"):
    if td.find('a') and re.match("show_detail", td.find('a')["onclick"]):
      # get votes id
      vote_id_match = re.search(r"\d{4,}", td.find('a')["onclick"])
      if vote_id_match:
          votings_ids.append(int(vote_id_match.group(0)))

  return votings_ids

def scrap_sestion_text(soup):
    session_texts = []
    for td in soup.find_all("td"):
        a_element = td.find('a')
        if a_element and re.search("สมัยสามัญ", a_element.text):
            # get sestion text
            session = a_element.text
            session_texts.append(session.strip())
    return session_texts

def scrap_meeting_ids(
    parliament_number, 
    latest_id, 
    start_year:int|None=None,
    stop_year:int|None=None
):
    
    meeting_id_list = []
    joined_meeting_id_list = []
    
    # ประชุม สส.
    def get_meeting_ids():
        _meeting_id_list = []
        for year in range(4, 0, -1): # count down from 4th year
            
            for parliament_session in ["วิสามัญ", "สมัยสามัญประจำปีครั้งที่สอง", "สมัยสามัญประจำปีครั้งที่หนึ่ง"]:
                session_response = request_meeting_records(parliament_number, year, parliament_session)
                
                soup = BeautifulSoup(BeautifulSoup(session_response.content, "html.parser").decode(), "html.parser")
                # Check pagination
                pagination_number = get_pagination_number(soup)
                # Get votings ids
                record_ids = []
                for page in range(1, pagination_number + 1):
                    session_response = request_meeting_records(parliament_number, year, parliament_session, page)
                    soup = BeautifulSoup(BeautifulSoup(session_response.content, "html.parser").decode(), "html.parser")
                    record_ids.extend(scrap_votings_id(soup=soup))
                if len(record_ids) == 0:
                    continue
                
                _meeting_id_list.extend([_id for _id in record_ids if _id > latest_id])

                if min(record_ids) <= latest_id:
                    print(f"\nmsbisID from สส \n{_meeting_id_list}\n")
                    return _meeting_id_list
                
                time.sleep(3) # delay to prevent exceed request limit
        print(f"\nmsbisID from สส \n{_meeting_id_list}\n")
        return _meeting_id_list
    meeting_id_list = get_meeting_ids()
    
    # ประชุมร่วม
    # Setup start and stop year
    if start_year is None:
        from datetime import datetime
        start_year = datetime.now().year # start from current year
        start_year += 543 # convert to Buddhist Era (BE)
    if stop_year is None:
        stop_year = start_year - 4 # scrape back 4 years
        
    def get_joint_meeting_ids():
        _meeting_id_list=[]
        for year in range(start_year, stop_year, -1): # count down from current year
            
            # get sestion text
            main_session_txt = "ข้อมูลการประชุมร่วมกันของรัฐสภา"
            main_session_response = request_joint_meeting_records(year, main_session_txt, level=3)
            soup = BeautifulSoup(BeautifulSoup(main_session_response.content, "html.parser").decode(), "html.parser")
            # Check pagination
            pagination_number = get_pagination_number(soup)
            # Get votings ids
            joint_meet_sestion = []
            for page in range(1, pagination_number + 1):
                main_session_response = request_joint_meeting_records(year, main_session_txt, level=3, page=page)
                soup = BeautifulSoup(BeautifulSoup(main_session_response.content, "html.parser").decode(), "html.parser")
                joint_meet_sestion.extend(scrap_sestion_text(soup))
            time.sleep(5)
            
            print(f"session in txt of joint meeting\n{joint_meet_sestion}\n")
            for parliament_session in joint_meet_sestion:
                session_response = request_joint_meeting_records(year, parliament_session)
                
                soup = BeautifulSoup(BeautifulSoup(session_response.content, "html.parser").decode(), "html.parser")
                record_ids = scrap_votings_id(soup=soup)
                if len(record_ids) == 0:
                    continue
                
                _meeting_id_list.extend([_id for _id in record_ids if _id > latest_id])
                
                if min(record_ids) <= latest_id:
                    print(f"\nmsbisID from ประชุมร่วม \n{_meeting_id_list}\n")
                    return _meeting_id_list
                
                time.sleep(3) # delay to prevent exceed request limit
        print(f"\nmsbisID from ประชุมร่วม \n\n{_meeting_id_list}\n")
        return _meeting_id_list
    
    joined_meeting_id_list = get_joint_meeting_ids()
    
    # sort ids
    return sorted(meeting_id_list), sorted(joined_meeting_id_list)
