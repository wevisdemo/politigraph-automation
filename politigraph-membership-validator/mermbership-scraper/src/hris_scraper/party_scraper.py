import re
import requests
from bs4 import BeautifulSoup

HRIS_URL = "https://hris.parliament.go.th/manage/system/user_present/show_plasma11_disp.php"

def clean_party_name(party_name):
    # Clean bracket
    cleaned_name = re.sub(r"\(.*\)", "", party_name).strip()
    return cleaned_name

def get_parties_info() -> list:
    
    response = requests.get(HRIS_URL)
    soup = BeautifulSoup(BeautifulSoup(response.content, "html.parser").decode(), "html.parser")
    
    party_info_table_header = soup.find('div', string=re.compile(r"ข้อมูลสมาชิกฯ แยกตามพรรคการเมือง"))
    if not party_info_table_header:
        return []
    
    # Get info table
    party_info_table = party_info_table_header.find_next_sibling().find('table')
    party_info_data = []
    for row in party_info_table.find_all('tr', {'class': 'h_detail'}):
        party_info = row.find_all('td')
        
        party_name = party_info[0].text
        party_total_count = int(party_info[-2].text)
        
        # Get party id
        info_link_element = party_info[-1].find('a')
        party_id = int(re.search(r"(\d+)", info_link_element['onclick']).group(1))
        
        party_info_data.append({
            'party_name': clean_party_name(party_name),
            'party_id': party_id,
            'total_count': party_total_count
        })
    
    return party_info_data