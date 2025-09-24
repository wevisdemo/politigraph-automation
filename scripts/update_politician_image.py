# /// script
# requires-python = "==3.10.11"
# dependencies = [
#     "opencv-python",
#     "pillow",
#     "thai-name-normalizer", "poliquery",
#     "python-dotenv",
#     "google-auth>=2.16.0",
#     "google-auth-oauthlib",
#     "google-auth-httplib2",
#     "google-api-python-client>=2.78.0",
#     "cachetools==5.5.2",
# ]
#
# [tool.uv.sources]
# thai-name-normalizer = { path = "../politigraph-name-normalizer", editable = true }
# poliquery = { path = "../politigraph-poliquery", editable = true }
# ///

import os
import re
from dotenv import load_dotenv

from google.auth import default
from googleapiclient.discovery import build

from poliquery import update_politician_image_url
from .image_files_manager import read_and_save_images_from_drive

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

def main():
    
    print("Reading and cropping politician images from Google Drive...")
    
    load_dotenv()  # take environment variables

    POLITICIAN_PHOTOS_DRIVE_FOLDER_ID=os.getenv('POLITICIAN_PHOTOS_DRIVE_FOLDER_ID')
    if not POLITICIAN_PHOTOS_DRIVE_FOLDER_ID:
        raise ValueError("Missing Drive folder ID...")
    
    credentials, _ = default(scopes=SCOPES)
    service = build("drive", "v3", credentials=credentials)
    
    POLITICIAN_IMAGES_DIR_PATH = "tmp/cropped-politician-images"
    
    # Read & Crop politician images from Google Drive
    read_and_save_images_from_drive(
        service, 
        POLITICIAN_PHOTOS_DRIVE_FOLDER_ID, 
        output_dir_path=POLITICIAN_IMAGES_DIR_PATH
    )
    
    # Update politician images url in Polotigraph
    for file in os.listdir(POLITICIAN_IMAGES_DIR_PATH):
        
        # Get politician first and last name from file name
        name = re.sub(r"\..*$", "", file)  # Remove file extension
        print(f"Updating image for {name}...")
        
        # Update the image URL in Politigraph
        update_politician_image_url(
            name=name,
            image_url=f"https://politigraph.wevis.info/assets/people/{file}"
        )
        print(f"Updated image URL for {name} to https://politigraph.wevis.info/assets/people/{file}")
        
if __name__ == "__main__":
    main()