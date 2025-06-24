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
from poliquery import get_apollo_client, update_politician_image_url, update_party_logo_image_url

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

def list_files_in_drive_folder(service, folder_id):
    """Lists file names in a given Google Drive folder."""
    query = f"'{folder_id}' in parents and (mimeType='image/jpeg' or mimeType='image/png')"
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
    else:
        print("Files in folder:")
        for file in files:
            print(f"{file['name']} (ID: {file['id']})")
    
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

def read_and_save_images_from_drive(
    service, 
    drive_folder_id:str, 
    output_dir_path:str="tmp/cropped-politician-images",
    crop:bool=True
):
    """Crops and updates politician images in a Google Drive folder."""
    
    # Create output directory if it does not exist
    os.makedirs(output_dir_path, exist_ok=True)
    
    files = list_files_in_drive_folder(service, drive_folder_id)
    
    for file in files[:5]: # TODO remove this limit in production
        file_id = file['id']
        file_name = file['name']
        
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


def main():
    
    load_dotenv()  # take environment variables

    POLITICIAN_PHOTOS_DRIVE_FOLDER_ID=os.getenv('POLITICIAN_PHOTOS_DRIVE_FOLDER_ID')
    PARTY_LOGOS_DRIVE_FOLDER_ID=os.getenv('PARTY_LOGOS_DRIVE_FOLDER_ID')
    
    POLITIGRAPH_SUBSCRIBTION_ENDPOINT = os.getenv("POLITIGRAPH_SUBSCRIBTION_ENDPOINT")
    POLITIGRAPH_TOKEN = os.getenv("POLITIGRAPH_TOKEN")
    
    credentials, _ = default(scopes=SCOPES)
    service = build("drive", "v3", credentials=credentials)
    
    POLITICIAN_IMAGES_DIR_PATH = "tmp/cropped-politician-images"
    PARTY_LOGOS_DIR_PATH = "tmp/cropped-party-logos"
    
    # Read & Crop politician images from Google Drive
    print("Reading and cropping politician images from Google Drive...")
    read_and_save_images_from_drive(
        service, 
        POLITICIAN_PHOTOS_DRIVE_FOLDER_ID, 
        output_dir_path=POLITICIAN_IMAGES_DIR_PATH
    )
    
    # Update politician images url in Polotigraph
    apollo_client = get_apollo_client(
        POLITIGRAPH_SUBSCRIBTION_ENDPOINT,
        POLITIGRAPH_TOKEN
    )
    import re
    for file in os.listdir(POLITICIAN_IMAGES_DIR_PATH):
        
        # Get politician first and last name from file name
        name = re.sub(r"\..*$", "", file)  # Remove file extension
        firstname = name.split("-")[0]
        lastname = " ".join(name.split("-")[1:])
        print(f"Updating image for {firstname} {lastname}...")
        
        # Update the image URL in Politigraph
        update_politician_image_url(
            client=apollo_client,
            firstname=firstname, 
            lastname=lastname, 
            image_url=f"https://politigraph.wevis.info/assets/people/{file}"
        )
        print(f"Updated image URL for {firstname} {lastname} to https://politigraph.wevis.info/assets/people/{file}")
        
    # Read & Save party logos from Google Drive
    print("Reading and cropping party logos from Google Drive...")
    read_and_save_images_from_drive(
        service, 
        PARTY_LOGOS_DRIVE_FOLDER_ID, 
        output_dir_path=PARTY_LOGOS_DIR_PATH,
        crop=False  # Don't crop party logos, just save them
    )
    # Update parties image url in Polotigraph
    apollo_client = get_apollo_client(
        POLITIGRAPH_SUBSCRIBTION_ENDPOINT,
        POLITIGRAPH_TOKEN
    )
    for file in os.listdir(PARTY_LOGOS_DIR_PATH):
        
        # Get party name from file name
        party_name = re.sub(r"\..*$", "", file)  # Remove file extension
        print(f"Updating logo for {party_name}...")
        
        # Update the image URL in Politigraph
        update_party_logo_image_url(
            client=apollo_client,
            party_name=party_name, 
            image_url=f"https://politigraph.wevis.info/assets/organizations/political-parties/{file}"
        )
        print(f"Updated logo URL for {party_name} to https://politigraph.wevis.info/assets/organizations/political-parties/{file}")
    
if __name__ == "__main__":
    main()