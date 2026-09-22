import os, shutil, time, json
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
import urllib.request
from functools import wraps
import cv2
import tarfile
import easyocr
import numpy as np
from typhoon_ocr import ocr_document

def ensure_min_duration(seconds=2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            result = func(*args, **kwargs)  # Run the actual function
            
            elapsed_time = time.perf_counter() - start_time
            remaining_time = seconds - elapsed_time
            
            if remaining_time > 0:
                time.sleep(remaining_time)
                
            return result
        return wrapper
    return decorator

class TyphoonReader:
    def __init__(
        self, 
    ):  
        load_dotenv()
       
    @ensure_min_duration(2) 
    def recognize(self, image: np.ndarray) -> str:
        # Create a temporary file that automatically closes/deletes
        with NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
            temp_path = temp.name
            cv2.imwrite(temp_path, image)
            print(f"Temporary JPG saved at: {temp_path}")
            
            # Recognize text
            markdown_result = ocr_document(
                pdf_or_image_path=temp_path,
                api_key=os.getenv('TYPHOON_OCR_API_KEY', '')
            )
            return markdown_result
            
        return ''

class OCRManager():
    
    _easyocr_instance = None
    _typhoon_instance = None

    EASYOCR_DIR = "models/thai-vl"
    EASYOCR_URL = (
        "https://github.com/napatswift/naplog/releases/download/v0.0.1/thai-vl.tar.gz"
    )
    
    @staticmethod
    def _download_and_extract(url: str, dest_dir: str, expected_file: str):
        if os.path.exists(expected_file):
            return

        os.makedirs(dest_dir, exist_ok=True)
        print(f"Downloading from {url}...")

        tar_path = os.path.join(dest_dir, "temp_model_archive")
        try:
            urllib.request.urlretrieve(url, tar_path)
            print("Extracting...")
            with tarfile.open(tar_path, "r:*") as tar_ref:
                tar_ref.extractall(path=dest_dir)

            # Remove the tar file first so it doesn't interfere with our check below
            os.remove(tar_path)

            # Smart flattening: If the archive unpacked into a single nested folder, bring contents up
            extracted_items = os.listdir(dest_dir)
            if len(extracted_items) == 1:
                single_item = os.path.join(dest_dir, extracted_items[0])
                if os.path.isdir(single_item):
                    for item in os.listdir(single_item):
                        shutil.move(os.path.join(single_item, item), dest_dir)
                    os.rmdir(single_item)

        except Exception as e:
            if os.path.exists(tar_path):
                os.remove(tar_path)
            raise RuntimeError(f"Failed to download or extract the model: {e}")

    @classmethod
    def get_easyocr(cls) -> easyocr.Reader:
        if cls._easyocr_instance is None:
            expected_file = os.path.join(cls.EASYOCR_DIR, "thai-vl.pth")
            cls._download_and_extract(cls.EASYOCR_URL, cls.EASYOCR_DIR, expected_file)

            cls._easyocr_instance = easyocr.Reader(
                ["th"],
                recog_network="thai-vl",
                user_network_directory=cls.EASYOCR_DIR,
                model_storage_directory=cls.EASYOCR_DIR,
                detector=False,
                gpu=True,
                verbose=False,
            )
        return cls._easyocr_instance
    
    @classmethod
    def get_typhoon_ocr(cls) -> TyphoonReader:
        if cls._typhoon_instance is None:
            cls._typhoon_instance = TyphoonReader()
        
        return cls._typhoon_instance