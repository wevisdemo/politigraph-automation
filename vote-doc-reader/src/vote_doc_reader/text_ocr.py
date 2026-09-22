import os
from dotenv import load_dotenv
import cv2
import numpy as np
import numpy.typing as npt
from .page_img_helper import detect_bboxes
from .ocr_manager import OCRManager
from .text_helper import extract_max_number, extract_date_from_text

def trim_line_whitespace(line_image: npt.NDArray, padding=10) -> npt.NDArray:
    if len(line_image.shape) == 3:
        gray = cv2.cvtColor(line_image, cv2.COLOR_BGR2GRAY)
    else:
        gray = line_image.copy()
    if np.std(gray) == 0:
        return line_image

    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    vertical_projection = np.sum(binary, axis=0)
    if vertical_projection is None:
        return line_image

    non_zero_cols = np.where(vertical_projection > 0)[0]

    if len(non_zero_cols) == 0:
        return line_image

    start_x = max(0, non_zero_cols[0] - padding)
    end_x = min(line_image.shape[1], non_zero_cols[-1] + padding + 1)

    return line_image[:, start_x:end_x]

def read_numbers(images: list[npt.NDArray], separator: str = "\n") -> str:
    if not images:
        return ""
    
    reader = OCRManager.get_easyocr()
    result_texts = []
    
    for _img in images:
        # 1. Base safety check: if the original array is somehow empty, skip it
        if _img is None or _img.size == 0:
            continue
            
        img = trim_line_whitespace(_img)
        
        # 2. FALLBACK: If trimming caused an empty image, revert to the original
        if img is None or img.size == 0:
            img = _img
            
        # 3. Ensure Color Channel Compatibility
        if img.dtype != np.uint8:
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)

        # Remove Alpha channel if it exists (4 channels down to 3)
        if len(img.shape) == 3 and img.shape[2] == 4:
            # Note: OpenCV default is BGRA, but if your image is RGBA use cv2.COLOR_RGBA2RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) 
            
        # 4. Safely extract text (prevents IndexError if no text is found)
        results = reader.recognize(img, blocklist="""¢£¤¥!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZกขคฆงจฉชซฌญฎฏฐฑฒณดตถทธนบปผฝพฟภมยรลวศษสหฬอฮฤเแโใไะาุูิีืึั่้๊๋็์ำํฺฯๆ""")
        
        if results:
            text = results[0][1] # type: ignore
            result_texts.append(text)
            
    return separator.join(result_texts).strip()

def read_texts(images: list[npt.NDArray], separator: str = "\n") -> str:
    if not images:
        return ""
    
    reader = OCRManager.get_easyocr()
    result_texts = []
    
    for _img in images:
        # 1. Base safety check: if the original array is somehow empty, skip it
        if _img is None or _img.size == 0:
            continue
            
        img = trim_line_whitespace(_img)
        
        # 2. FALLBACK: If trimming caused an empty image, revert to the original
        if img is None or img.size == 0:
            img = _img
            
        # 3. Ensure Color Channel Compatibility
        if img.dtype != np.uint8:
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)

        # Remove Alpha channel if it exists (4 channels down to 3)
        if len(img.shape) == 3 and img.shape[2] == 4:
            # Note: OpenCV default is BGRA, but if your image is RGBA use cv2.COLOR_RGBA2RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) 
            
        # 4. Safely extract text (prevents IndexError if no text is found)
        results = reader.recognize(img, blocklist="¢£¤¥ฺ")
        
        if results:
            text = results[0][1] # type: ignore
            result_texts.append(text)
            
    return separator.join(result_texts)

def read_texts_typhoon(images: list[npt.NDArray], separator: str = "\n") -> str:
    
    load_dotenv()
    
    if os.getenv('TYPHOON_OCR_API_KEY') is None:
        return read_texts(images, separator=separator)
        
    # Read with typhoon
    reader = OCRManager.get_typhoon_ocr()
    result_texts = []
    for _img in images:
        # 1. Base safety check: if the original array is somehow empty, skip it
        if _img is None or _img.size == 0:
            continue
            
        img = trim_line_whitespace(_img)
        
        # 2. FALLBACK: If trimming caused an empty image, revert to the original
        if img is None or img.size == 0:
            img = _img
            
        # 3. Ensure Color Channel Compatibility
        if img.dtype != np.uint8:
            if img.max() <= 1.0:
                img = (img * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)

        # Remove Alpha channel if it exists (4 channels down to 3)
        if len(img.shape) == 3 and img.shape[2] == 4:
            # Note: OpenCV default is BGRA, but if your image is RGBA use cv2.COLOR_RGBA2RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR) 
        # 4. Safely extract text (prevents IndexError if no text is found)
        results = reader.recognize(img)
        
        if results:
            text = results # type: ignore
            result_texts.append(text)
                    
    return separator.join(result_texts)

def detect_and_read_text(
    image: npt.NDArray, 
    separator:str="\n", 
    use_typhoon:bool=False
) -> str:
    
    # Detect bboxes
    text_bboxes = detect_bboxes(image)
    # Filter noise
    text_bboxes = [
        bb for bb in text_bboxes if bb[2]-bb[0] > 40 and bb[3]-bb[1] > 40
    ]
    text_bboxes.sort(key=lambda bb: bb[1])
    
    text_images = [
        image[y1:y2, x1:x2] for x1, y1, x2, y2 in text_bboxes
    ]
    
    if use_typhoon:
        result_text = read_texts_typhoon(text_images, separator=separator)
    else:
        result_text = read_texts(text_images, separator=separator)
    
    return result_text

def read_text_in_row_data(row_images_data: list[dict[str,list[npt.NDArray]]]) -> list[dict[str,str]]:

    result_data = []
    for row in row_images_data:
        result_data.append({
            'order': read_numbers(row.get('order', [])),
            'member_num': read_numbers(row.get('member_num', [])),
            'voter_name': read_texts(row.get('voter_name', []), separator=" "),
            'party_name': read_texts(row.get('party_name', [])),
            'vote_option': read_texts(row.get('vote_option', [])),
        })
    
    return result_data

def read_info_text(info_data_images: dict[str,npt.NDArray]) -> dict[str, str|int]:
    
    info_data = {}
    # Read image into data dict
    for key, img in info_data_images.items():
        info_data[key] = read_texts([img])
        
    # Save row date text
    raw_date_text = info_data.get('date', '')
    for key, txt in info_data.items():
        info_data[key] = extract_max_number(txt)
    # Extract date
    info_data['date'] = extract_date_from_text(raw_date_text)
    
    return info_data