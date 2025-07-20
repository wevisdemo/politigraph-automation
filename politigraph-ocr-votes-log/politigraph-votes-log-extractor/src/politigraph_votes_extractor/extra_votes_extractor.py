import cv2
import numpy as np
import numpy.typing as npt
import pandas as pd

from PIL import Image
from pdf2image import convert_from_path, pdfinfo_from_path

from .image_processing import process_to_gray_scale
from .bbox_helper import convert_rect_to_bbox

# TODO combine function with normal dilate & parse k_size instead
def dilate_text_full_horizontal(image:Image) -> npt.ArrayLike:
    gray_im = process_to_gray_scale(image)
    gray_im = np.array(gray_im)
    
    blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
    th, threshed = cv2.threshold(
        blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    erode = cv2.erode(threshed, np.ones((5,5), np.uint8), iterations=1)
    
    _, w = gray_im.shape
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(w//2, 1))

    threshed = cv2.dilate(erode, kernel)
    dilated = cv2.dilate(threshed, kernel)
    
    return dilated

# TODO combine function with normal dilate & parse k_size instead
def dilate_text_horizontal(image:Image):
    gray_im = process_to_gray_scale(image)
    gray_im = np.array(gray_im)
    
    blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
    th, threshed = cv2.threshold(
        blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    erode = cv2.erode(threshed, np.ones((5,5), np.uint8), iterations=1)
    
    _, w = gray_im.shape
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(w//7, 1))

    threshed = cv2.dilate(erode, kernel)
    dilated = cv2.dilate(threshed, kernel)
    
    return dilated

def detect_row_bbox(dilated:npt.ArrayLike):
    contours, hier = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    rects = [cv2.boundingRect(c) for c in contours]
    # Filter out small text rects
    rects = [r for r in rects if r[3] > 20]
    
    bboxs = [convert_rect_to_bbox(r) for r in rects]
    return bboxs

def detect_table_in_btm_page(
    image:Image,
    row_bboxes:list,
    min_col:int=3,
    width_threshold:int=100
) -> list:
    rows = []
    for row_bbox in row_bboxes:
        croped_image = image.crop((row_bbox))
        gray_im = process_to_gray_scale(croped_image)
        gray_im = np.array(gray_im)
        
        blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
        th, threshed = cv2.threshold(
            blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        
        h, _ = gray_im.shape
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(25, h))

        threshed = cv2.dilate(threshed, kernel)
        dilated = cv2.dilate(threshed, kernel)
        
        detected_bboxes = detect_row_bbox(dilated)
        # Filter out noises
        detected_bboxes = [bb for bb in detected_bboxes if bb[2]-bb[0] > width_threshold]
        
        # Detect Table
        _breaker = False
        if len(detected_bboxes) > min_col:
            _breaker = True
            # contruct new bbox to have the same y1 & y2
            rows.append([
                (bb[0], row_bbox[1], bb[2], row_bbox[3]) for bb in detected_bboxes
            ])
        elif _breaker:
            break
    
    return rows

def crop_bottom_out(image:Image, crop_margin:int=25):
    width, height = image.size
    return image.crop((crop_margin, crop_margin, width-crop_margin, height*0.9))

def extract_bottom_page(image:Image) -> Image:
    
    # Crop & Detect bbox
    cropped_btm_image = crop_bottom_out(image)
    
    dilated = dilate_text_horizontal(cropped_btm_image)
    bboxes = detect_row_bbox(dilated)
    
    # Sort from bottom up
    bboxes.sort(key=lambda bbox: bbox[1], reverse=True)
    
    w, h = cropped_btm_image.size
    
    # Get the second bbox from bottom that end before half of the page
    _trigger = False
    half_page_width = w // 2
    stop_bbox = None
    for bbox in bboxes:
        _, _, x2, _ = bbox
        if x2 < half_page_width:
            if _trigger:
                stop_bbox = bbox
                break
            _trigger = True
    
    # Crop bottom page out
    if not stop_bbox:
        return image
    return image.crop((0, stop_bbox[1], w, h))

def detect_btm_table_rows_bboxes(image: Image):
    
    dilated = dilate_text_full_horizontal(image)
    
    row_bboxes = detect_row_bbox(dilated)
    # Pad bbox TODO remove magic number
    row_bboxes = [(bb[0], bb[1]-15, bb[2], bb[3]+15) for bb in row_bboxes]
    
    # For each row dilate and detect columns
    # if there are more than 3 column extract data
    rows = detect_table_in_btm_page(image, row_bboxes)
    
    return rows

def extract_extra_votes(pdf_file_path: str, reader=None) -> pd.DataFrame:
    
    assert reader, "OCR Reader Not Found!!"
    
    # Get pdf info
    _pdf_info = pdfinfo_from_path(pdf_file_path)
    last_page = _pdf_info['Pages']
    
    # Convert to images
    pdf_images = convert_from_path(pdf_file_path, dpi=300, first_page=last_page)
    image = pdf_images[0]
    
    # Crop only bottom page
    btm_page = extract_bottom_page(image)
    
    rows = detect_btm_table_rows_bboxes(btm_page)
    
    # Iterate over each row read data from last column to contruct dict
    btm_img = np.array(btm_page)
    data = []
    for row in rows:
        sorted_row = sorted(row, key=lambda bb: bb[0], reverse=True)
        row_data = []
        for bbox in sorted_row[:3]:
            _x1, _y1, _x2, _y2 = bbox
            _text = reader.recognize(
                btm_img[_y1:_y2, _x1:_x2]
            )[0][1] # ocr text from textbox
            row_data.append(_text)
        data.append(row_data)
    
    extra_votes_df = pd.DataFrame(data, columns=['ผลการลงคะแนน', 'ชื่อสังกัด', 'ชื่อ - สกุล'])
        
    return extra_votes_df[['ชื่อ - สกุล', 'ชื่อสังกัด', 'ผลการลงคะแนน']]

