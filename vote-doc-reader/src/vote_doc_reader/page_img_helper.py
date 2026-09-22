import time
import cv2
import numpy as np
import numpy.typing as npt
from itertools import pairwise

def get_white_column_ranges(image_array: npt.NDArray, margin_percent: int = 15):
    """
    Finds ranges of columns that are completely white (255) 
    within the content area (excluding margins).
    """
    img = np.array(image_array)
    width = img.shape[1]
    
    # Calculate margin in pixels
    margin = int(width * (margin_percent / 100))
    
    # Slice the image to ignore margins
    content_area = img[:, margin : width - margin]
    
    # Identify white columns in the sliced content area
    is_white_col = np.all(content_area == 255, axis=0)
    
    # Find transitions
    padded = np.concatenate(([False], is_white_col, [False]))
    diffs = np.diff(padded.astype(int))
    
    # Find start/end indices relative to the CONTENT_AREA
    starts_in_content = np.where(diffs == 1)[0]
    ends_in_content = np.where(diffs == -1)[0]
    
    # Offset the indices back to original image coordinates
    # We add the margin back to map the content-indices to full-image-indices
    starts = starts_in_content + margin
    ends = ends_in_content + margin
    
    return list(zip(starts, ends - 1))

def detect_bboxes(image: npt.NDArray) -> list[tuple[int, int, int, int]]:
    
    _, thresh = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    kernel = np.ones((15, 50), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bboxes = []
    for cnt in contours:
        if cv2.contourArea(cnt) > 200:  # Filter small noise
            x, y, w, h = cv2.boundingRect(cnt)
            
            bboxes.append((x, y, x + w, y + h))

    return bboxes

def merge_bboxes(bboxes: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int]:
    return (
        min([_[0] for _ in bboxes]),
        min([_[1] for _ in bboxes]),
        max([_[2] for _ in bboxes]),
        max([_[3] for _ in bboxes]),
    )

def detect_lines_bbox(image: npt.NDArray) -> list[tuple[int, int, int, int]]:
    _, threshed = cv2.threshold(
            image, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    kernel = np.ones((5, image.shape[1]), np.uint8)
    dilated = cv2.dilate(threshed, kernel, iterations=1)
    # import time
    # cv2.imwrite("dialted.jpg", dilated)
    # time.sleep(1.5)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bboxes = []
    for cnt in contours:
        if cv2.contourArea(cnt) > 200:  # Filter small noise
            x, y, w, h = cv2.boundingRect(cnt)
            
            bboxes.append((x, y, x + w, y + h))

    return bboxes
    
    
def get_top_section(page: npt.NDArray) -> npt.NDArray:
    
    page_height, page_width = page.shape
    # Get top-right corner of page
    top_right_page = page[:, page_width//2:]
    
    bboxes = detect_bboxes(top_right_page)
    bboxes = [
        bb for bb in bboxes if (bb[2] - bb[0]) > 200 and bb[0] > (page_width//2)//2
    ]
    
    bboxes.sort(key=lambda bb: bb[1])
    
    cropped = page[:bboxes[0][1]-5, :]
    
    return cropped
    
def get_title_section(page: npt.NDArray) -> npt.NDArray:
    
    top_section = get_top_section(page)
    
    white_columns = get_white_column_ranges(top_section)
    # Filter white column
    white_columns = [
        wc for wc in white_columns if wc[1] - wc[0] > 50
    ]
    
    if white_columns:
        split_x = int(white_columns[0][0] + (white_columns[0][1] - white_columns[0][0])/2)
        return top_section[:, split_x:]
    
    return top_section[:, top_section.shape[1]//2:]


def get_info_section(page: npt.NDArray):
    
    top_section = get_top_section(page)
    
    white_columns = get_white_column_ranges(top_section)
    # Filter white column
    white_columns = [
        wc for wc in white_columns if wc[1] - wc[0] > 50
    ]
    
    if white_columns:
        split_x = int(white_columns[0][0] + (white_columns[0][1] - white_columns[0][0])/2)
        return top_section[:, :split_x]
    
    return top_section[:, top_section.shape[1]//2:]

def get_info_data_images(info_image: npt.NDArray) -> dict[str,npt.NDArray]:
    
    # Detect lines
    line_bboxes = detect_lines_bbox(info_image)
    line_bboxes = [bb for bb in line_bboxes if bb[3]-bb[1] > 30]
    line_bboxes.sort(key=lambda bb: bb[1])
    
    if len(line_bboxes) < 6: # skip if found less than 6 row
        return {}
    
    line_images = []
    for line_bbox in line_bboxes:
        _, y1, _, y2 = line_bbox
        line_images.append(info_image[y1:y2, :])
    
    return {
        'date': line_images[-6],
        'attendance': line_images[-5],
        'agree': line_images[-4],
        'disagree': line_images[3],
        'abstain': line_images[-2],
        'novote': line_images[-1],
    }

def detect_column_range(line_image: npt.NDArray):
    _, thresh = cv2.threshold(line_image, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    kernel = np.ones((line_image.shape[0], 50), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    # 1. Create a boolean array where white pixels are True (assuming 255 is white)
    is_white = (dilated[line_image.shape[0]//2] == 255)

    # 2. Pad with False at both ends to catch segments starting/ending at the edges
    padded = np.hstack([False, is_white, False])

    # 3. Find where the boolean values change (transitions)
    diff = np.diff(padded.astype(int))

    # Start positions are where diff == 1
    start_indices = np.where(diff == 1)[0]

    # End positions are where diff == -1 (subtract 1 because of padding/inclusive index)
    end_indices = np.where(diff == -1)[0] - 1

    # Combine into intervals (start, end)
    segments = list(zip(start_indices, end_indices))
    
    segments = [
        (int(r[0]), int(r[1])) for r in segments
    ]
    
    return segments 
 
def get_table_image(page: npt.NDArray) -> npt.NDArray:
    
    # Crop top part
    page_height, page_width = page.shape
    # Get top-right corner of page
    top_right_page = page[:page_height//2, page_width//2:]
    
    bboxes = detect_bboxes(top_right_page)
    bboxes = [
        bb for bb in bboxes if (bb[2] - bb[0]) > 200 and bb[0] > (page_width//2)//2
    ]
    start_crop_y = 0
    if bboxes:
        bboxes.sort(key=lambda bb: bb[1])
        start_crop_y = bboxes[0][3] + 5
    cropped = page[start_crop_y:int(page_height*0.9), :]
    
    # Crop ผู้ปฏิบัติหน้าที่ประธานในที่ประชุม
    line_bboxes = detect_lines_bbox(cropped)
    line_bboxes.sort(key=lambda bb: bb[1])
    for line_bbox in line_bboxes:
        x1, y1, x2, y2 = line_bbox
        line_img = cropped[y1:y2, x1:x2]
        # cv2.imwrite("line.jpg", line_img)
        # time.sleep(1)
        _bboxes = detect_bboxes(line_img)
        # Filter bbox
        _bboxes = [
            bb for bb in _bboxes if bb[3] - bb[1] > 20
        ]
        if not _bboxes:
            break
        # Get the right most bbox to crop ผู้ปฏิบัติหน้าที่ประธานในที่ประชุม / หมายเหตุ
        _bboxes.sort(key=lambda bb: bb[2])
        right_most_bb = _bboxes[-1]
        if right_most_bb[0] < int(page_width*0.20) and right_most_bb[2] < page_width//2:
            cropped = cropped[:y1-5, :]
            break
        
        # Get the left most bbox to crop 
        left_most_bb = _bboxes[0]
        # Crop at `กลุ่มรายงานการประชุม...`
        if left_most_bb[2] > int(page_width*0.8):
            cropped = cropped[:y1-5, :]
            break
        # Crop at `เครื่องหมาย - (ยติภังค์)...`
        elif left_most_bb[0] < int(page_width*0.20) and left_most_bb[2] > int(page_width*0.5):
            cropped = cropped[:y1-5, :]
            break
        
    return cropped

def get_rows_images_in_table(image: npt.NDArray) -> list[dict[str,list[npt.NDArray]]]:
    
    _, page_width = image.shape
    
    row_image_data: list[dict[str, list[npt.NDArray]]] = []
    
    line_bboxes = detect_lines_bbox(image)
    line_bboxes.sort(key=lambda bb: bb[1])
    
    column_x_ranges = []
    for line_bbox in line_bboxes[1:]:
        _, y1, _, y2 = line_bbox
        line_image = image[y1-5:y2+5, 0:page_width]
        
        # Detect bboxes
        detect_col_ranges = detect_column_range(line_image)
        if len(detect_col_ranges) == 5:
            # Define the continuous split points (boundaries)
            boundaries = [
                detect_col_ranges[0][0] - 15,                     # Leftmost edge
                *[col[0] - 10 for col in detect_col_ranges[1:]],  # Middle splits
                detect_col_ranges[-1][1] + 15                     # Rightmost edge
            ]
            # Pair them up into (start, end) tuples
            column_x_ranges = list(pairwise(boundaries))
            break
    
    if not column_x_ranges:
        return []
    # output_img = image.copy()
    # for x1, x2 in column_x_ranges:
    #     cv2.rectangle(output_img, (x1, 15), (x2, page_height-15), (0, 255, 0))
    # cv2.imwrite("col.jpg", output_img)
    # time.sleep(1)
    for line_idx, line_bbox in enumerate(line_bboxes[1:]):
        
        _, y1, _, y2 = line_bbox
        row_images = []
        for x1, x2 in column_x_ranges:
            row_images.append(
                image[y1-5:y2+5, x1:x2]
            )
        order_img = row_images[0]
        member_num_img = row_images[1]
        voter_name_img = row_images[2]
        party_name_img = row_images[3]
        vote_option_img = row_images[4]
        
        # Handle double line row
        row_bboxes = detect_bboxes(line_image)
        row_bboxes = [bb for bb in row_bboxes if bb[3]-bb[1] > 30] # Filter noise
        if len(row_bboxes) == 1 and 0 < line_idx < len(line_bboxes) - 2:
            row_image_data[-1]['voter_name'].append(voter_name_img)
            continue    
        
        row_image_data.append({
            'order': [order_img],
            'member_num': [member_num_img],
            'voter_name': [voter_name_img],
            'party_name': [party_name_img],
            'vote_option': [vote_option_img],
        })
    
    return row_image_data

def get_extra_votes_images(page:npt.NDArray) -> list[dict[str,list[npt.NDArray]]]:
    
    # Crop top part
    page_height, page_width = page.shape
    # Get top-right corner of page
    top_right_page = page[:page_height//2, page_width//2:]
    
    bboxes = detect_bboxes(top_right_page)
    bboxes = [
        bb for bb in bboxes if (bb[2] - bb[0]) > 200 and bb[0] > (page_width//2)//2
    ]
    start_crop_y = 0
    if bboxes:
        bboxes.sort(key=lambda bb: bb[1])
        start_crop_y = bboxes[0][3] + 5
    cropped = page[start_crop_y:int(page_height*0.9), :]
    
    # Crop to be only table
    line_bboxes = detect_lines_bbox(cropped)
    line_bboxes.sort(key=lambda bb: bb[1])
    
    detected_note_lines = []
    
    for line_bbox in line_bboxes:
        x1, y1, x2, y2 = line_bbox
        line_img = cropped[y1:y2, x1:x2]
        _bboxes = detect_bboxes(line_img)
        # Filter bbox
        _bboxes = [
            bb for bb in _bboxes if bb[3] - bb[1] > 20
        ]
        if not _bboxes:
            continue
        # Get the right most bbox to crop ผู้ปฏิบัติหน้าที่ประธานในที่ประชุม / หมายเหตุ
        _bboxes.sort(key=lambda bb: bb[2])
        right_most_bb = _bboxes[-1]
        if right_most_bb[0] < int(page_width*0.20) and right_most_bb[2] < page_width//2:
            detected_note_lines.append(line_bbox)
    
    if len(detected_note_lines) != 2:
        return []
    
    detected_note_lines.sort(key=lambda bb: bb[1])
    table_image = cropped[
        detected_note_lines[0][3]+5:detected_note_lines[-1][1]-5,
        :
    ]
    
    # Extract images from each row
    line_bboxes = detect_lines_bbox(table_image)
    line_bboxes.sort(key=lambda bb: bb[1])
    column_x_ranges = []
    for line_bbox in line_bboxes[::-1]:
        _, y1, _, y2 = line_bbox
        line_image = table_image[y1-5:y2+5, 0:page_width]
        
        # Detect bboxes
        detect_col_ranges = detect_column_range(line_image)
        if 4 <= len(detect_col_ranges) <= 5:
            boundaries = [
                detect_col_ranges[0][0] - 15,                     # Leftmost edge
                *[col[0] - 10 for col in detect_col_ranges[1:]],  # Middle splits
                detect_col_ranges[-1][1] + 15                     # Rightmost edge
            ]
            # Pair them up into (start, end) tuples
            column_x_ranges = list(pairwise(boundaries))
            break
    
    row_image_data = []
    for line_bbox in line_bboxes[1:]:
        _, y1, _, y2 = line_bbox
        row_images = []
        for x1, x2 in column_x_ranges:
            row_images.append(
                table_image[y1-5:y2+5, x1:x2]
            )
    
        # Reverse row        
        row_images.reverse()
        row_images += [None] * (5 - len(row_images))
        
        order_img = row_images[4]
        member_num_img = row_images[3]
        voter_name_img = row_images[2]
        party_name_img = row_images[1]
        vote_option_img = row_images[0]
        
        row_image_data.append({
            'order': [order_img] if order_img is not None else [],
            'member_num': [member_num_img],
            'voter_name': [voter_name_img],
            'party_name': [party_name_img],
            'vote_option': [vote_option_img],
        })
    
    return row_image_data