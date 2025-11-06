import re
import cv2
from PIL import Image
import numpy as np
import numpy.typing as npt
from pdf2image import convert_from_path

from .pdf_converter import load_pdf_to_image
from .bbox_helper import convert_rect_to_bbox, detect_text_bbox, group_bboxs_into_rows, filter_border_bboxes
from .image_processing import dilate_image_vertical, process_to_gray_scale
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

############################ NEW DETECTOR ############################

def dilate_text(image:Image, ksize=(20, 5), erode_k=(5,5)):
    gray_im = process_to_gray_scale(image)
    gray_im = np.array(gray_im)
    
    blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
    th, threshed = cv2.threshold(
        blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    erode = cv2.erode(threshed, np.ones(erode_k, np.uint8), iterations=1)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=ksize)

    threshed = cv2.dilate(erode, kernel)
    dilated = cv2.dilate(threshed, kernel)
    
    return dilated

def detect_bbox(dilated:npt.ArrayLike):
    contours, hier = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    rects = [cv2.boundingRect(c) for c in contours]
    # Filter out small text rects
    rects = [r for r in rects if r[3] > 20]
    
    bboxs = [convert_rect_to_bbox(r) for r in rects]
    return bboxs

def detect_rows_border(image:Image, padding:int=15) -> list:
    w, _ = image.size
    dilated = dilate_text(image, ksize=(w, 5))
    
    rows_borders = detect_bbox(dilated)
    # Sort from top to bottom (y1)
    rows_borders.sort(key=lambda bb: bb[1])
    rows_borders = [(bb[0], bb[1]-padding, bb[2], bb[3]+padding) for bb in rows_borders]
    return rows_borders

def crop_half_page(image:Image, crop_margin:int=25):
    w, h = image.size
    return image.crop((w//2, crop_margin, w-crop_margin, h-crop_margin))

def extract_page_header(image:Image) -> Image:
    half_page = crop_half_page(image)
    _, h = half_page.size
    
    rows_borders = detect_rows_border(half_page)
    
    # Go through rows until find one start before half of te width
    crop_y2_position = h//2
    for row_border in rows_borders:
        row_image = half_page.crop(row_border)
        _row_bboxes = detect_bbox(dilate_text(row_image, ksize=(25, row_image.size[1])))
        _row_bboxes.sort(key=lambda bb: bb[0]) # sort with x1

        _x1_fisrt_row = _row_bboxes[0][0] # x1 of bbox 1
        # If start of the box is start after half of row
        if _x1_fisrt_row > row_border[2]//2:
            crop_y2_position = row_border[1]
            break
        
    return image.crop((0, 0, image.size[0], crop_y2_position + 25))

def read_text_in_image(image:Image, reader=None) -> list:
    rows_border = detect_rows_border(image)
    rows_border.sort(key=lambda bb: bb[1])
    
    texts = ""
    for row_bd in rows_border:
        row_image = image.crop(row_bd)
        row_img = np.array(row_image)
        text_bbox = detect_bbox(dilate_text(row_image, ksize=(25, row_image.size[1]), erode_k=(2, 2)))
        text_bbox.sort(key=lambda bb: bb[0])
        for bbox in text_bbox:
            _x1, _y1, _x2, _y2 = bbox
            texts += reader.recognize(
                            row_img[_y1:_y2, _x1:_x2]
                        )[0][1] # ocr text from textbox
            texts += "\t"
        texts += "\n"
    
    return texts

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
    
def get_doc_data(
    image: Image, 
    reader=None,
    correct_validate_key: list=["จำนวนผู้เข้าร่วมประชุม", "เห็นด้วย", "ไม่เห็นด้วย", "งดออกเสียง", "ไม่ลงคะแนนเสียง"]
) -> dict:
    
    assert reader, "OCR Reader Not Found!!"
    
    # Extract page header
    header_image = extract_page_header(image)
    w, h = header_image.size
    
    # Split into validate side & title info type
    group_bboxes = detect_bbox(dilate_text(header_image, ksize=(40, h)))
    # Filter small bbox out
    group_bboxes = [bb for bb in group_bboxes if bb[2]-bb[0] > w*0.20]
    group_bboxes.sort(key=lambda bb: bb[0])
    
    # Get validate data
    validate_table_bbox = group_bboxes[0]
    validate_table_image = header_image.crop(validate_table_bbox)
    
    validation_text = read_text_in_image(validate_table_image, reader=reader)
    # validation_text = re.sub(r"\s+", " ", validation_text)
    validation_data = extract_validation_data(
        validation_text,
        correct_validate_key
    )
    # Check if it need to extract extra votes
    had_extra_vote = False
    if re.search(r"\d+\s+?\+\s+?\d+", validation_text):
        had_extra_vote = True
    
    doc_data = {} # TODO change to bill data
    doc_data['date'] = None
    doc_data['validation_data'] = validation_data
    doc_data['had_extra_votes'] = had_extra_vote
    return doc_data

def extract_doc_data(pdf_file_path: str, reader=None) -> dict:
    assert reader, "OCR Reader Not Found!!"
    
    pdf_image = load_pdf_to_image(pdf_file_path, dpi=300, last_page=1)[0]
    print(f"Extract validate data from {pdf_file_path}...")
    
    doc_data = get_doc_data(pdf_image, reader=reader)
    
    print(doc_data)
    
    return doc_data
    