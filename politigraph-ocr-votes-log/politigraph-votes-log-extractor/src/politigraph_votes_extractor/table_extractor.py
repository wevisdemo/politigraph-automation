import time
import numpy as np
import numpy.typing as npt
import cv2
from PIL import Image

from .bbox_helper import detect_text_bbox, filter_border_bboxes, group_bboxs_into_rows, normalize_table_bbox

def get_column_index(bbox, bbox_row: list, thres: int=5):
    x1, _, _, _ = bbox
    for index, _bbox in enumerate(bbox_row):
        if x1 > (_bbox[0] - thres):
            return index
    return -1

def extract_data_from_table(table_img: npt.ArrayLike, reader=None):
    
    table_image = Image.fromarray(table_img)
    
    # Start timer to check time take to execute
    _start = time.time()
    
    # Detect text rects
    text_bboxs = detect_text_bbox(table_image)

    # Filter out bboxes that close to page border
    h, w, _ = table_img.shape
    text_bboxs = filter_border_bboxes(text_bboxs, h, w)
    # Filter out small bbox
    # text_bboxs = [bb for bb in text_bboxs if bb[3]-bb[1]>20]
    def get_size(bbox):
        return (bbox[2]-bbox[0])*(bbox[3]-bbox[1])
    text_bboxs = [bbox for bbox in text_bboxs if get_size(bbox) > 1000]
    # Filter out large bbox
    text_bboxs = [bb for bb in text_bboxs if bb[3]-bb[1]<200]

    # Sort text rects
    text_bboxs = sorted(text_bboxs, key=lambda bb: bb[1])
    
    # Group text rects into rows
    text_rows = group_bboxs_into_rows(text_bboxs)

    # Trim row with less than 5 columns out
    while len(text_rows) >= 2 and len(text_rows[0]) < 5:
        text_rows = text_rows[1:]
    while len(text_rows) >= 3 and any(len(_r) < 4 for _r in text_rows[-3:]): # Use 4 instead of 5 for case of '-' at last row
        text_rows = text_rows[:-1]

    if len(text_rows) < 2: # No data to ocr
        return [["", "", "", "", ""]]
        
    try:
        text_rows = normalize_table_bbox(text_rows)
    except Exception as e:
        return[["", "", "", "", ""]]
    finally:
        _end = time.time()
        print(f"Detect bbox completes, took: {_end - _start:.2f} sec")
    
    _start = time.time()
    # Read text from each row
    table_texts_data = []
    for index, row in enumerate(text_rows):
        if len(row) < 5:
            # if first or last row, skip
            if index == 0 or index == (len(text_rows) - 1):
                continue
            
        row_texts = []
        for bbox in row:
            _x1, _y1, _x2, _y2 = bbox
            text = reader.recognize(
                table_img[_y1:_y2, _x1:_x2]
            )[0][1] # ocr text from textbox
            row_texts.append(text)
        table_texts_data.append(row_texts)
    _end = time.time()
    print(f"OCR texts completed, took: {_end - _start:.2f} sec")    
    
    return table_texts_data