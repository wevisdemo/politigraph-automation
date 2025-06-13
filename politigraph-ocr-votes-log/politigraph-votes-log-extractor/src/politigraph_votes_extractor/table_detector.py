import cv2
from PIL import Image
import numpy as np

from .image_processing import process_to_gray_scale
from .bbox_helper import convert_rect_to_bbox

def dilate_image(image: Image, iterations=16):
    
    gray_im = process_to_gray_scale(image)
    gray_im = np.array(gray_im)
    
    blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
    th, threshed = cv2.threshold(
        blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    large_dilate_kernel: tuple = (25, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, large_dilate_kernel)
    
    threshed = cv2.dilate(threshed, kernel)

    dilated = cv2.dilate(threshed, kernel, iterations = iterations)
    return dilated

def detect_blocks(image: Image) -> list:
    """Detects blocks in the image using contour detection."""
    
    dialated = dilate_image(image)
    contours, hier = cv2.findContours(
        dialated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    rects = [cv2.boundingRect(c) for c in contours]
    return [convert_rect_to_bbox(r) for r in rects]

def pad_table(table_bbox, h, w):
    x1, y1, x2, y2 = table_bbox
    return [
        max(0, x1-15), 
        max(0, y1-15), 
        min(w, x2+15), 
        min(h, y2+15)
    ]

def get_table_bbox(image: Image, index:int=1) -> list:
    """Get tables in the image using contour detection."""
    
    blocks = detect_blocks(image)
    
    # Remove any block that less than 75% of page width
    h, w, _ = np.array(image).shape
    filtered_blocks = [bb for bb in blocks if bb[2]-bb[0] > (w*0.75)]
    filtered_blocks = [bb for bb in filtered_blocks if bb[3]-bb[1] > 120] # Filter out small blocks
    if len(filtered_blocks) == 0: # Detect no big table return the whole page
        h, w, _ = np.array(image).shape
        return (20, 20, w-20, h-20)
    
    # If it is first page pick the last table to ignore validate table
    _reversed = False
    if index == 0:
        _reversed = True
    blocks = sorted(filtered_blocks, key=lambda bb: bb[1], reverse=_reversed) # sort bt y1
    biggest_block = blocks[0]
    
    return pad_table(biggest_block, h, w)