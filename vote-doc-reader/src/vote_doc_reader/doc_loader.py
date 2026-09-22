import pymupdf
import cv2
import numpy as np
import numpy.typing as npt

def fill_borders(image: np.ndarray, margin: float = 0.03, color=None) -> npt.NDArray:
    img = image.copy()
    h, w = img.shape[:2]
    
    pad_h = int(round(h * margin))
    pad_w = int(round(w * margin))
    
    if color is None:
        color = 1.0 if np.issubdtype(img.dtype, np.floating) else 255
        
    if pad_h > 0:
        img[:pad_h, :] = color
        img[h - pad_h:, :] = color
    if pad_w > 0:
        img[:, :pad_w] = color
        img[:, w - pad_w:] = color
        
    return img  

def load_pdf_images(pdf_path: str) -> list[npt.NDArray]:
    doc = pymupdf.open(pdf_path)
    
    page_images = []
    for page in doc:
        pix = page.get_pixmap(colorspace=pymupdf.csRGB, alpha=False, dpi=300)
        img_rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        
        # Extract only the Red channel (index 0 in RGB)
        # Both the white paper (R=255) and red watermark (R=200-255) are bright here
        red_channel = img_rgb[:, :, 0]
        
        # Use Otsu's thresholding so it dynamically adapts to the page contrast
        _, thresh = cv2.threshold(red_channel, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        page_img = cv2.bitwise_not(thresh)
        filled_border_page = fill_borders(page_img)
        page_images.append(filled_border_page)
        
    return page_images