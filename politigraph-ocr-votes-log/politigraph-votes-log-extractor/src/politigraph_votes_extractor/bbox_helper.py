import cv2
from typing import List, Tuple
from PIL import Image

from .image_processing import process_to_gray_scale, noise_removal

def convert_rect_to_bbox(rect):
    x, y, w, h = rect
    return (x, y, x+w, y+h)

def filter_border_bboxes(
        bboxes: list,
        h, w,
        threshold: int=15
):
    return [
        bb for bb in bboxes
        if bb[0] > threshold
        and bb[1] > threshold
        and bb[0] < w-threshold
        and bb[1] < h-threshold
    ]

def detect_text_bbox(
    image: Image,
    small_dilate_kernel: tuple = (5, 5), 
    large_dilate_kernel: tuple = (25, 5)
    ) -> list:
    
    gray_im = process_to_gray_scale(image)
    gray_im = noise_removal(gray_im)
    
    # detect text bbox
    blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
    th, threshed = cv2.threshold(
        blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, small_dilate_kernel)
    threshed = cv2.dilate(threshed, kernel)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, large_dilate_kernel)
    dilated = cv2.dilate(threshed, kernel)
    contours, hier = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    rects = [cv2.boundingRect(c) for c in contours]
    # Filter out small text rects
    rects = [r for r in rects if r[3] > 20]
    
    bboxs = [convert_rect_to_bbox(r) for r in rects]

    return bboxs

# Define a type alias for clarity
Bbox = List[int]

def is_y_overlapped(bb_a, bb_b, tolerance:float=5) -> bool:
    min_y = bb_b[0] - tolerance
    max_y = bb_b[1] + tolerance
    if (min_y <= bb_a[0] <= max_y) or (min_y <= bb_a[1] <= max_y):
        return True
    return False

def group_bboxs_into_rows(
    bboxes: List[Bbox],
) -> List[List[Bbox]]:
    
    sorted_y_bboxes = sorted(bboxes, key=lambda bb: bb[1])
    
    rows = []
    
    max_y = 0
    for bbox in sorted_y_bboxes:
        if bbox[1] > max_y:
            rows.append([bbox]) # Create new row
            max_y = bbox[3]
            continue
        for i in range(-1, (len(rows)+1)*-1, -1):
            y_min = min([bb[1] for bb in rows[i]])
            y_max = max([bb[3] for bb in rows[i]])
            if is_y_overlapped((bbox[1], bbox[3]), (y_min, y_max)):
                rows[i].append(bbox)
                rows = sorted(
                    rows,
                    key=lambda row: min([bb[1] for bb in row])
                )
                break
                
    return rows

def merge_overlapping_intervals(intervals):
    if not intervals:
        return []

    # Create sorted list
    sorted_intervals = sorted(intervals, key=lambda x: x[0])

    merged_intervals = []
    # Add the first interval to start the merging process
    merged_intervals.append(list(sorted_intervals[0])) # Use list for mutability

    for i in range(1, len(sorted_intervals)):
        current_start, current_end = sorted_intervals[i]
        last_merged_start, last_merged_end = merged_intervals[-1]

        # If the current interval's start is less than or equal to the last merged interval's end
        if current_start <= last_merged_end:
            # Overlap exists, merge them by updating the end of the last merged interval
            # The new end is the maximum of the current interval's end and the last merged interval's end
            merged_intervals[-1][1] = max(last_merged_end, current_end)
        else:
            # No overlap, add the current interval as a new one
            merged_intervals.append(list(sorted_intervals[i])) # Add as a new list

    # Convert inner lists back to tuples if desired for the output format
    return [tuple(interval) for interval in merged_intervals]

def normalize_table_bbox(
    rows_bbox: list, 
    y_padding:int=5,
    last_row_threshold:float=0.3
) -> List[Tuple]:
    
    # Get x y range from every bbox
    x_intervals = []
    for row in rows_bbox:
        for bbox in row:
            x_intervals.append((bbox[0], bbox[2]-5)) # Crop to prevent x2 spiling
            
    columns_range = merge_overlapping_intervals(x_intervals)
            
    assert len(columns_range) == 5, f"Expected range to be 5 got: {len(columns_range)}"
    
    normalized_rows_bbox = []
    for index, row in enumerate(rows_bbox):
        # print(row)
        min_y = min([bb[1] for bb in row])
        max_y = max([bb[3] for bb in row])
        # If the last row is significantly larger than previous row
        # then it is row with signature signed
        if index == len(rows_bbox)-1: # last row
            prev_row_height = normalized_rows_bbox[-1][0][3] - normalized_rows_bbox[-1][0][1]
            last_row_height = max_y - min_y
            if (last_row_height-prev_row_height) > (prev_row_height*last_row_threshold):
                max_y = min_y + (prev_row_height-(y_padding*2))
        normalized_rows_bbox.append(
            [(_x[0], min_y-y_padding, _x[1]+5, max_y+y_padding) for _x in columns_range]
        )
    
    return normalized_rows_bbox
