from typing import List
import os, re
from io import BytesIO
import cv2
from PIL import Image

import numpy as np

def list_files_in_drive_folder(service, folder_id):
    """Lists file names in a given Google Drive folder."""
    query = f"'{folder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png' or mimeType='image/jpg')"
    files = []
    page_token = None
    while True:
        response = (
            service.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
            )
            .execute()
        )
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken", None)
        # If there is no next page, break the loop
        if page_token is None:
            break
    
    if not files:
        print("No files found in the folder.")
        return []
    
    return files

def load_image(service, file_id):
    """Function to download an image as a PIL Image object"""
    request = service.files().get_media(fileId=file_id)
    file_data = request.execute()
    image = Image.open(BytesIO(file_data))  # Open image with PIL from in-memory bytes
    return image

def crop_center(pil_img):
    # Image size
    img_width, img_height = pil_img.size
    
    short_size = min(img_width, img_height)
    
    # Define the crop box centered around the face
    start_x = max((img_width // 2) - (short_size // 2), 0)
    end_x = min((img_width // 2) + (short_size // 2), img_width)
    start_y = max((img_height // 2) - (short_size // 2), 0)
    end_y = min((img_height // 2) + (short_size // 2), img_height)
    
    cropped_image = pil_img.crop((start_x, start_y, end_x, end_y))
    
    return cropped_image

def crop_image(pil_img, zoom_factor=1.7):
    # Image size
    img_width, img_height = pil_img.size
    
    # Detect face
    # Convert PIL Image to OpenCV format (NumPy array)
    image_cv = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    # Load the Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml') # type: ignore
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
      print("No face detected.")
      return crop_center(pil_img) # Detected no faces, return and just crop center
    
    # Get first detected face position
    x_face, y_face, w_face, h_face = faces[0]
    
    # Determine the crop dimensions centered on the face
    face_center_x = x_face + w_face // 2
    face_center_y = y_face + h_face // 2
    
    half_crop_size = int(max(w_face, h_face) * zoom_factor) // 2 # 1.7 is hard code zoom facter
    
    # Define the crop box centered around the face
    start_x = max(face_center_x - half_crop_size, 0)
    end_x = min(face_center_x + half_crop_size, img_width)
    start_y = max(face_center_y - half_crop_size, 0)
    end_y = min(face_center_y + half_crop_size, img_height)
    
    # Crop the image to the square region in PIL format
    cropped_image = pil_img.crop((start_x, start_y, end_x, end_y))
    
    return cropped_image

def read_and_save_images_from_drive(
    service, 
    drive_folder_id:str, 
    output_dir_path:str="tmp/cropped-politician-images",
    crop:bool=True,
    select_names:List[str]=[],
):
    """Crops and updates politician images in a Google Drive folder."""
    
    # Create output directory if it does not exist
    os.makedirs(output_dir_path, exist_ok=True)
    
    files = list_files_in_drive_folder(service, drive_folder_id)
    
    if select_names:
        print(f"Selected names:\n{select_names}")
        
    for file in files:
        file_id = file['id']
        file_name = file['name']
        
        if select_names:
            import re
            _name = re.sub(r"\..*", "", file_name) # remove file extension
            if _name not in select_names:
                continue
        
        print(f"Process file: {file_name}...")
        
        # Raname file to be PNG
        import re
        if not file_name.endswith('.webp'):
            file_name = re.sub(r"\..*$", ".webp", file_name)
        
        # Check if the image is already exists
        # This is only for local testing, not for production
        output_file_path = os.path.join(output_dir_path, file_name)
        if os.path.exists(output_file_path):
            print(f"Image {file_name} already exists in {output_dir_path}, skipping cropping.")
            continue
        
        # Load the image
        image = load_image(service, file_id)
        
        # Crop the image
        if crop and "cropped" not in file_name.lower():
            image = crop_image(image)
        image.save(output_file_path, 'webp', optimize=True, quality=90)
        print(f"Cropped and saved image: {file_name} to {output_file_path}")

