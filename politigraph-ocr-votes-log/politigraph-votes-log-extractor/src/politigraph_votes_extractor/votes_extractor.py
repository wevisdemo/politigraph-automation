import numpy as np
import pandas as pd
from pdf2image import convert_from_path

from .pdf_converter import load_pdf_to_image
from .table_detector import get_table_bbox
from .table_extractor import extract_data_from_table
from .typo_cleaner import is_header_valid
from .df_cleaner import clean_votelog_df

def extract_votelog(pdf_file_path: str, reader=None) -> pd.DataFrame:
    
    assert reader, "OCR Reader Not Found!!"
    
    pdf_images = load_pdf_to_image(pdf_file_path, dpi=300)
    print(f"Extract votelog from {pdf_file_path}...")
    
    # Initiate base dataframe
    COLUMN_HEADER = ["ลําดับที่", "เลขที่บัตร", "ชื่อ - สกุล", "ชื่อสังกัด", "ผลการลงคะแนน"]
    votes_df = pd.DataFrame(
        columns=COLUMN_HEADER
    )
    
    for page_idx, page_image in enumerate(pdf_images):
        
        print(f"OCR doc page: {page_idx+1}")
        
        table_bbox = get_table_bbox(page_image, page_idx)
        x1, y1, x2, y2 = table_bbox
        page_img = np.array(page_image)
        
        table_data = extract_data_from_table(
            page_img[y1:y2, x1:x2],
            reader=reader
        )
        
        # Make first row a header
        if is_header_valid(table_data[0], COLUMN_HEADER):
            table_data.pop(0)
        
        _new_votes_df = pd.DataFrame.from_records(
            table_data,
            columns=COLUMN_HEADER
        )
        votes_df = pd.concat(
            [votes_df, _new_votes_df],
            ignore_index=True
        )
        
    return votes_df
        