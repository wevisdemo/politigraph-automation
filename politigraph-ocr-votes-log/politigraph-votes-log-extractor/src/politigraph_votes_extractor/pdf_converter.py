from typing import List
from PIL.Image import Image
import fitz
from pdf2image import convert_from_bytes

def load_pdf_to_image(
    pdf_file_path: str,
    dpi: int=300,
    first_page: int|None=None,
    last_page: int|None=None,
    watermark_layer_name: str='Watermark'
) -> List[Image]:
    
    # Load doc
    doc = fitz.open(pdf_file_path)
    
    # Get all Optional Content Groups (layers)
    ocgs = doc.get_ocgs()

    # Find the xref of the watermark layer by its name
    watermark_xref = 0
    for xref, ocg in ocgs.items():
        if ocg.get("name") == watermark_layer_name:
            watermark_xref = int(xref)
            break

    if watermark_xref:
        # Disable the watermark layer in the default configuration
        doc.set_layer(-1, off=[watermark_xref])

    # Save the modified PDF to a memory buffer
    pdf_bytes = doc.write()
    doc.close()
    
    # Convert the PDF bytes to a list of PIL Image objects
    if first_page and last_page:
        images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=first_page, last_page=last_page)
    elif first_page:
        images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=first_page)
    elif last_page:
        images = convert_from_bytes(pdf_bytes, dpi=dpi, last_page=last_page)
    else:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)
    
    return images