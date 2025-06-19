# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client",
#     "opencv-python",
#     "pillow",
#     "poliquery",
#     "python-dotenv",
# ]
#
# [tool.uv.sources]
# poliquery = { path = "../politigraph-poliquery", editable = true }
# ///

from io import BytesIO
from PIL import Image
from google.auth import default
from googleapiclient.discovery import build

import os
import cv2
import numpy as np

from dotenv import load_dotenv

SCOPES = [
    "https://www.googleapis.com/auth/drive.appdata",
    "https://www.googleapis.com/auth/drive.appfolder"
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
]

def list_files_in_drive_folder(service, folder_id):
    """Lists file names in a given Google Drive folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    files = []
    page_token = None
    while True:
        response = (
            service.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
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
    else:
        print("Files in folder:")
        for file in files:
            print(f"{file['name']} (ID: {file['id']})")
    
    return files

def load_image(file_id, service):
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
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
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

def main():
    
    load_dotenv()  # take environment variables

    GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
    
    credentials, _ = default(scopes=SCOPES)
    service = build("drive", "v3", credentials=credentials)
    
    files = list_files_in_drive_folder(service, GOOGLE_DRIVE_FOLDER_ID)

if __name__ == "__main__":
    main()