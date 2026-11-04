import time

import cv2
import numpy.typing as npt
from google.cloud import vision


def detect_text_with_request(grayscale_array: npt.NDArray) -> tuple[list[dict], str]:
    # Initialize the client
    client = vision.ImageAnnotatorClient()

    # Encode the grayscale NumPy array into PNG bytes
    success, encoded_image = cv2.imencode('.png', grayscale_array)
    if not success:
        raise ValueError("Failed to encode the NumPy array into an image.")
    content = encoded_image.tobytes()

    # Create the Vision API Image object
    image = vision.Image(content=content)

    # Create the Feature object
    feature = vision.Feature(
        type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION
    )

    # Build the AnnotateImageRequest object
    request = vision.AnnotateImageRequest(
        image=image,
        features=[feature]
    )

    # Call the core annotate_image function!
    response = None
    _count = 0
    while _count < 5:
        try:
            response = client.annotate_image(request=request)
            break
        except:
            _count += 1
            time.sleep(5)
    assert response is not None

    # Handle errors
    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")

    # Extract text and bounding boxes into a list of dicts
    full_text = response.full_text_annotation.text

    # Get text paragraphs
    pages = response.full_text_annotation.pages
    if not pages:
        return [], full_text
    blocks = pages[0].blocks

    detected_text = []
    for block in blocks:
        # Combine text
        paragraphs = block.paragraphs
        for paragraph in paragraphs:
            for word in paragraph.words:
                # Get bbox
                points = word.bounding_box.vertices
                xs = [point.x for point in points]
                ys = [point.y for point in points]

                # Find the min and max values
                x1, y1 = min(xs), min(ys)
                x2, y2 = max(xs), max(ys)

                bbox = (x1, y1, x2, y2)
                text = "".join([_.text for _ in word.symbols])
                detected_text.append({
                    "text": text,
                    "bbox": bbox
                })

    return detected_text, full_text
