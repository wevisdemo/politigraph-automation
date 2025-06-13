import cv2
import numpy as np
import numpy.typing as npt
from PIL import Image

def process_to_gray_scale(image: Image) -> npt.ArrayLike:
    # Convert to gray scale
    image = image.convert('L')
    # Threshold
    threshold = 125
    image = image.point( lambda p: 255 if p > threshold else 0 )
    # To mono
    image = image.convert('1')
    image = image.convert('L')
    
    return np.array(image)

def noise_removal(image: npt.ArrayLike) -> npt.ArrayLike:
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.medianBlur(image, 3)
    return image

#### Validate Table ####
def dilate_image_vertical(image):
    
    gray_im = process_to_gray_scale(image)
    gray_im = np.array(gray_im)
    
    blured = cv2.GaussianBlur(gray_im, (9, 9), 0)
    th, threshed = cv2.threshold(
        blured, 200, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    h, w = gray_im.shape

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, ksize=(20, 2 * h))

    threshed = cv2.dilate(threshed, kernel)
    dilated = cv2.dilate(threshed, kernel)
    
    return dilated