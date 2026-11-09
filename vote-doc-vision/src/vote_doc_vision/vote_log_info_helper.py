import re

import cv2
from numpy.typing import NDArray

from .constants import THAI_MONTHS
from .google_vision_helper import detect_text_with_request
from .text_helper import combine_text_in_bboxes, combine_texts_group
from .votes_helper import clean_votes, extract_votes_data


def normalize_image(image: NDArray) -> NDArray:
    if len(image.shape) == 2:
        # Already a standard 2D grayscale image
        img = image
    elif image.shape[2] == 1:
        # 3D image with 1 channel -> squeeze it to 2D
        img = image.squeeze(axis=2)
    elif image.shape[2] == 4:
        # RGBA image (with alpha/transparency channel)
        img = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
    else:
        # Standard 3-channel RGB image
        img = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    return img

def get_classification(full_text: str, classification_type: str) -> str:

    if re.search(r"^ขอให้วุฒิสภาพิจารณา", full_text):
        return classification_type

    # Check วาระ
    # Get classification number
    CLASSIFICATION_MAP = {
        "1": 1, "๑": 1, "หนึ่ง": 1,
        "2": 2, "๒": 2, "สอง": 2,
        "3": 3, "๓": 3, "สาม": 3,
    }

    # วาระ 1-3
    classification_num = None
    match = re.search(r"วาระที่(หนึ่ง|สอง|สาม|[1-3๑-๓])", full_text)
    if match:
        classification_num = CLASSIFICATION_MAP.get(match.group(1)) if match else None
        return f"{classification_type}_{classification_num}"
    
    # พรก.    
    emergency_bill_match = re.search(r"อนุมัต(.|\n)+?พระราชก(\u0e4d\u0e32|\u0e33)หนด", full_text)
    if emergency_bill_match:
        classification_num = 1
        return f"{classification_type}_{classification_num}"
    
    senate_2_match = re.search(r"มาตรา\s?\d+(.|\n)+?(เพิ่มมาตรา|แก้ไข)(.|\n)+?คงไว้", full_text)
    if senate_2_match:
        classification_num = 2
        return f"{classification_type}_{classification_num}"
    
    return classification_type

def get_vote_date(full_text: str) -> str|None:

    day = None
    month = None
    year = None

    # Date
    day_match = re.search(r"วันที่\s?(\d+)", full_text)
    if day_match:
        day = day_match.group(1)

    # Month
    month_pattern = "|".join(THAI_MONTHS)
    month_match = re.search(r"(" + month_pattern + r")", full_text)
    if month_match:
        month = month_match.group(1)

    # Year
    year_match = re.search(r"พ\.ศ\.\s?(25\d{2})", full_text)
    if year_match:
        year = year_match.group(1)

    if all(_ is not None for _ in [day, month, year]):
        return f"{int(year)-543}-{str(THAI_MONTHS.index(month) + 1).zfill(2)}-{str(day).zfill(2)}" # type: ignore

def get_vote_count(full_text: str) -> dict:

    vote_count = {}

    # Attendence
    attendance_match = re.search(r"จำนวนผู้เข้าร่วม.+?(?:\s|\n)?(\d+)", full_text)
    if attendance_match:
        vote_count['attendance_count'] = int(attendance_match.group(1))

    # Agree
    agree_match = re.search(r"(?<!ไม่)เห็นด้วย(?:\s|\n)?(\d+)", full_text)
    if agree_match:
        vote_count['agree_count'] = int(agree_match.group(1))

    # Disagree
    disagree_match = re.search(r"ไม่เห็นด้วย(?:\s|\n)?(\d+)", full_text)
    if disagree_match:
        vote_count['disagree_count'] = int(disagree_match.group(1))

    # Abstain
    abstain_match = re.search(r"งดออกเสียง(?:\s|\n)?(\d+)", full_text)
    if abstain_match:
        vote_count['abstain_count'] = int(abstain_match.group(1))

    # Novote
    novote_match = re.search(r"ไม่ลงคะแนนเสียง(?:\s|\n)?(\d+)", full_text)
    if novote_match:
        vote_count['novote_count'] = int(novote_match.group(1))

    return vote_count

def extract_vote_log_info(
    page_img: NDArray,
    classification_type: str
) -> dict[str, str|int|list|None]:

    # Convert image to grayscale
    page_height, page_width = page_img.shape
    img = normalize_image(page_img)

    # Extract text with Google Vision
    detected_text_bboxes, full_text = detect_text_with_request(img[:int(page_height*0.95)])
    text_bboxes = combine_texts_group(detected_text_bboxes)

    title = None
    classification = get_classification(full_text, classification_type)
    vote_date = get_vote_date(full_text)

    # Identify start of the table
    table_start_bbox = next(
        (tt for tt in text_bboxes if re.search(r"ลำดับ|ชื่อสังกัด|ผลการลงคะแนน", tt.get('text', ''))),
        None
    )

    # Get vote title
    match_title = re.search(r"ร่าง(.|\n)+?(?=ซึ่ง)", full_text)
    if match_title:
        title = match_title.group(0)
        title = title.replace("\n", " ")
        title = title.strip()
    else: # Combine bbox of texts
        if table_start_bbox:
            # Filter text on the top right of page
            title_bboxes = [
                tt for tt in text_bboxes if tt.get('bbox',[])[0] > (page_width * 0.45) and tt.get('bbox', [])[3] < table_start_bbox.get('bbox', [])[1]
            ]
            title = combine_text_in_bboxes(title_bboxes)

    # Get vote count
    vote_count = get_vote_count(full_text)

    # Extract votes
    votes_bboxes = [
        tt for tt in text_bboxes if tt.get('bbox',[])[1] > table_start_bbox.get('bbox', [])[3] - 5
    ]

    votes_data = extract_votes_data(votes_bboxes)

    # Clean data
    votes_data = clean_votes(votes_data, full_text=full_text)

    return {
        'title': title,
        'classification': classification,
        'vote_date': vote_date,
        'attendance_count': vote_count.get('attendance_count', -1),
        'agree_count': vote_count.get('agree_count', -1),
        'disagree_count': vote_count.get('disagree_count', -1),
        'abstain_count': vote_count.get('abstain_count', -1),
        'novote_count': vote_count.get('novote_count', -1),
        'votes': votes_data
    }

def extract_votes(page_img: NDArray) -> list[dict]:

    # Convert image to grayscale
    page_height, _ = page_img.shape
    img = normalize_image(page_img)

    # Extract text with Google Vision
    detected_text_bboxes, full_text = detect_text_with_request(img[:int(page_height*0.95)])
    text_bboxes = combine_texts_group(detected_text_bboxes)

    # Identify start of the table
    table_start_bbox = next(
        (tt for tt in text_bboxes if re.search(r"ลำดับ|ชื่อสังกัด|ผลการลงคะแนน", tt.get('text', ''))),
        {}
    )

    # Extract votes
    votes_bboxes = [
        tt for tt in text_bboxes if tt.get('bbox',[0,0,0,0])[1] > table_start_bbox.get('bbox', [0,0,0,0])[3] - 5
    ]

    votes_data = extract_votes_data(votes_bboxes)

    # Clean data
    votes_data = clean_votes(votes_data, full_text=full_text)

    return votes_data
