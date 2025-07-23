import cv2
import numpy as np
import numpy.typing as npt
import pandas as pd

from PIL import Image
from pdf2image import convert_from_path, pdfinfo_from_path

from .image_processing import process_to_gray_scale
from .bbox_helper import convert_rect_to_bbox


def dilate_text(image:Image, ksize=(20, 5), erode_k=(5, 5)):
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

def detect_bbox_in_row(image:Image, row_border:tuple) -> list:
    x1, y1, _, _ = row_border
    row_image = image.crop(row_border)
    
    dilated = dilate_text(row_image, ksize=(20, row_image.size[1]), erode_k=(2, 2))
    bboxes = detect_bbox(dilated)
    
    return [
        (bb[0]+x1, bb[1]+y1, bb[2]+x1, bb[3]+y1) for bb in bboxes
    ]
    
def crop_bottom_out(image:Image, crop_margin:int=25):
    width, height = image.size
    return image.crop((crop_margin, crop_margin, width-crop_margin, height*0.9))

def detect_table_in_btm_page(image:Image) -> list:
    
    cropped_btm_image = crop_bottom_out(image)
    dilated = dilate_text(
        cropped_btm_image,
        ksize=(cropped_btm_image.size[0], 10),
        erode_k=(10, 10)
    )

    rows_borders = detect_bbox(dilated)
    rows_borders.sort(key=lambda bb: bb[1])
    
    # Get all bbox in each row
    rows_bbox = []
    for row_border in rows_borders:
        rows_bbox.append(
            sorted(detect_bbox_in_row(cropped_btm_image, row_border),
                key=lambda bb: bb[0] # sort with x1
            )
        )
        
    # Get only further bbox
    w, h = cropped_btm_image.size
    _bboxes = []
    for row in rows_bbox:
        if len(row) > 1:
            continue
        if row[0][2] < w//4: # end of bbox is less than 20% of page
            _bboxes.append(row[0])
    if not _bboxes:
        return cropped_btm_image # detected no table
    footnote_bbox = sorted(_bboxes, key=lambda bb: bb[1])[0]
    
    return cropped_btm_image.crop((0, footnote_bbox[3], w, h))

def extract_btm_table_data(image:Image, reader=None, padding:int=15):
    dilated = dilate_text(
        image,
        ksize=(image.size[0], 10),
        erode_k=(10, 10)
    )

    rows_borders = detect_bbox(dilated)
    rows_borders.sort(key=lambda bb: bb[1])
    
    # Read data in each row
    data = []
    img = np.array(image)
    for row_border in rows_borders:
        row_data = []
        row_bboxes = sorted(detect_bbox_in_row(image, row_border),
            key=lambda bb: bb[2], # sort with x2
            reverse=True
        )
        if len(row_bboxes) < 3: # skip any row that less than 3 columns
            continue
        # Pad bbox:
        row_bboxes = [
            (bb[0], 
             bb[1] - padding if bb[1] - padding >= 0 else 0, 
             bb[2], 
             bb[3] + padding) for bb in row_bboxes
        ]
        for bbox in row_bboxes:
            _x1, _y1, _x2, _y2 = bbox
            row_data.append(
                reader.recognize(
                    img[_y1:_y2, _x1:_x2]
                )[0][1] # ocr text from textbox
            )
        data.append(row_data[:3])
        
    
    return data

def extract_extra_votes(pdf_file_path: str, reader=None) -> pd.DataFrame:
    
    # assert reader, "OCR Reader Not Found!!"
    
    # Get pdf info
    _pdf_info = pdfinfo_from_path(pdf_file_path)
    last_page = _pdf_info['Pages']
    
    # Convert to images
    pdf_images = convert_from_path(pdf_file_path, dpi=300, first_page=last_page)
    image = pdf_images[0]
    
    btm_table_image = detect_table_in_btm_page(image)
    btm_table_data = extract_btm_table_data(btm_table_image, reader=reader)
    extra_votes_df = pd.DataFrame(btm_table_data, columns=['ผลการลงคะแนน', 'ชื่อสังกัด', 'ชื่อ - สกุล'])
    return extra_votes_df[['ชื่อ - สกุล', 'ชื่อสังกัด', 'ผลการลงคะแนน']]