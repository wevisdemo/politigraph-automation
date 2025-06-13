import re
import cv2
from PIL import Image
import numpy as np
import numpy.typing as npt
from pdf2image import convert_from_path

from .bbox_helper import convert_rect_to_bbox, detect_text_bbox, group_bboxs_into_rows, filter_border_bboxes
from .image_processing import dilate_image_vertical
from .table_detector import detect_blocks
from .typo_cleaner import correct_typo

def get_page_header_fallback(image: Image):
    
    detected_blocks = detect_blocks(image)
    biggest_bbox = sorted(
        detected_blocks,
        key=lambda bb: bb[2]-bb[0],
        reverse=True
    )[0]
    
    img = np.array(image)
    
    _, y1, _, _ = biggest_bbox
    return Image.fromarray(img[0:y1, :])
    
def get_page_header(image: Image):
    
    img = np.array(image)
    h, w, _ = img.shape
    cropped_img = img[:, w//2:w]
    cropped_image = Image.fromarray(cropped_img)
    
    # Detect and filter text bboxes
    detected_bbox = detect_text_bbox(cropped_image)
    detected_bbox = [bbox for bbox in detected_bbox if bbox[3] - bbox[1] > 40]
    detected_bbox = filter_border_bboxes(detected_bbox, h, w, threshold=15)
    
    # Get only bbox with x1 > w/2
    h, w, _ = cropped_img.shape
    detected_bbox = [bbox for bbox in detected_bbox if bbox[0] > w//2]
    
    if not detected_bbox:
        return get_page_header_fallback(image)
    
    # Get the first bbox
    _, y1, _, _ = sorted(detected_bbox, key=lambda bb: bb[1])[0]
    
    return Image.fromarray(
        img[0:y1, :]
    )

def detect_validate_table(image: Image):
    dialated = dilate_image_vertical(image)
    contours, hier = cv2.findContours(
        dialated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rects = [cv2.boundingRect(c) for c in contours]
    return [convert_rect_to_bbox(r) for r in rects]

def get_validate_tables(image: Image):
    
    header_image = get_page_header(image)
    header_img = np.array(header_image)
    _, w, _ = header_img.shape
    
    v_tables = detect_validate_table(header_image)
    # Sort out any small detected tables
    v_tables = [bb for bb in v_tables if bb[2]-bb[0] > 200]
    v_tables.sort(
        key=lambda bb: (w-bb[0], bb[2]-bb[0]),
        reverse=True
    )
    
    validate_tables = []
    for table_bbox in v_tables:
        x1, y1, x2, y2 = table_bbox
        validate_tables.append(
            Image.fromarray(header_img[y1:y2, x1:x2])
        )
    
    return validate_tables

def extract_info_text(
    image: Image, 
    reader=None
):
    bboxes = detect_text_bbox(
        image,
        # small_dilate_kernel=(12, 12)
    )
    bboxes = [bb for bb in bboxes if bb[3]-bb[1] > 30] # Filter out small bboxes
    
    img = np.array(image)
    
    rows = group_bboxs_into_rows(bboxes)
    result_text = ""
    for row in rows:
        for bbox in row:
            _x1, _y1, _x2, _y2 = bbox
            _text = reader.recognize(
                img[_y1-5:_y2+5, _x1:_x2]
            )[0][1]
            result_text += _text + "    "
        result_text += "\n"
    
    return result_text

def extract_date_from_text(validate_data_text):
    # TODO extract date from text
    return ""

def extract_max_number(text):
    number_str = re.findall(r"\d{1,}", text)
    return max([int(n) for n in number_str] + [-1])

def extract_validation_data(
    validate_data_text,
    correct_keyword: list=["จำนวนผู้เข้าร่วมประชุม", "เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"]
):
    validate_data_text = re.sub(r"[^\u0E00-\u0E7F\s\.\d\(\)\/]", "", validate_data_text)
    
    
    # Extract Validate Data
    CORRECT_VALIDATE_KEY = correct_keyword
    
    # Check if วันที or พ.ศ. present in table, if not: wrong table
    if not re.search(r"(วัน|พ\.ศ\.|เวลา)", validate_data_text):
        return {_key:-1 for _key in CORRECT_VALIDATE_KEY}
    
    validate_data = {}
    for validate_line in validate_data_text.splitlines():
        
        # Check if '' present if so extract date instead
        if re.search(r"(วัน|พ\.ศ\.|เวลา|เรื่อง)", validate_line):
            continue
        
        # Get only Thai text
        if not re.search(
            r"([\u0E00-\u0E7F]?.*[\u0E00-\u0E7F](\s|\d))", 
            validate_line
        ): # No Thai text in this line
            continue
        validate_key = re.search(
            r"([\u0E00-\u0E7F]?.*[\u0E00-\u0E7F](\s|\d))", 
            validate_line
        ).group(1)
        # Clean special characters
        validate_key = re.sub("\t", "", validate_key).strip()
        
        # Correct typo
        validate_key = correct_typo(
            validate_key,
            CORRECT_VALIDATE_KEY,
            similarity_threshold=80 # reduce threshold to 80
        )
        
        # Extract number to pair with key
        validate_data[validate_key] = extract_max_number(validate_line)
    
    return validate_data

def extract_bill_data(name_info_text):
    
    # Check if วาระ is present in table, if not: wrong table
    if not re.search(r"วาระ.*\d{1}", name_info_text):
        return {
            'bill_title': re.sub("\n", " ", name_info_text).strip(),
            'vote_event_type': "อื่นๆ"
        }
    
    # Extract vote type
    vote_type = re.search(r"วาระ.*\d{1}", name_info_text).group(0)
    bill_name = re.search(r"(.|\n)*(?=วาระ)", name_info_text).group(0)
    
    vote_type = re.sub(
        r"([\u0E00-\u0E7F])(\d)", 
        r"\1 \2",
        vote_type
    )
    
    bill_name = re.sub(r"(\n|\t)", " ", bill_name).strip()
    bill_name = re.sub(r"\s{1,}", " ", bill_name)
    
    return {
        'bill_title': bill_name,
        'vote_event_type': vote_type
    }

def get_doc_data(
    image: Image, 
    reader=None,
    correct_validate_key: list=["จำนวนผู้เข้าร่วมประชุม", "เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"]
):
    
    # Detect validate table
    detected_validation_tables = get_validate_tables(image)
    if len(detected_validation_tables) == 1:
        print("Warning: Detected only 1 info group!!")
        # If found just one table use both to find validate
        _tab = detected_validation_tables[0]
        detected_validation_tables = [_tab, _tab]
    elif len(detected_validation_tables) > 2:
        print("Warning: Detected more than 2 info groups!!") # proceed as usual
    elif len(detected_validation_tables) < 2:
        print("Warning: No table detected!!") # proceed as usual
        return {
            'bill_title': "",
            'vote_event_type': "",
            'date': "",
            'validation_data': {
                _key:-1 for _key in correct_validate_key
            }
        }
    
    # First table contain validate data
    validation_table_image = detected_validation_tables[0]
    # Second table contain name and vote_type
    name_info_table_image = detected_validation_tables[1]
    
    validation_text = extract_info_text(validation_table_image, reader=reader)
    name_info_text = extract_info_text(name_info_table_image, reader=reader)
    
    # Clean special characters
    name_info_text = re.sub(r"[^\u0E00-\u0E7F\s\.\d\(\)\/]", "", name_info_text)
    
    # Extract Validate Data
    validation_data = extract_validation_data(
        validation_text,
        correct_keyword=correct_validate_key
    )
    
    # Extract Bill Data(name, vote_type)
    bill_data = extract_bill_data(name_info_text)
    
    # Extract Date
    date = extract_date_from_text(validation_text)
    
    # print(validation_data)
    # print(bill_data)
    # print(date)
    
    doc_data = bill_data
    doc_data['date'] = date
    doc_data['validation_data'] = validation_data
    return doc_data
    
def extract_doc_data(pdf_file_path: str, reader=None) -> dict:
    assert reader, "OCR Reader Not Found!!"
    
    pdf_image = convert_from_path(pdf_file_path, dpi=300, last_page=1)[0]
    print(f"Extract validate data from {pdf_file_path}...")
    
    doc_data = get_doc_data(pdf_image, reader=reader)
    
    return doc_data
    