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

from poliquery import update_party_logo_image_url
from .image_files_manager import read_and_save_images_from_drive

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

def main():
    
    print("Reading and cropping party logos from Google Drive...")
    
    load_dotenv()  # take environment variables

    PARTY_LOGOS_DRIVE_FOLDER_ID=os.getenv('PARTY_LOGOS_DRIVE_FOLDER_ID')
    if not PARTY_LOGOS_DRIVE_FOLDER_ID:
        raise ValueError("Missing Drive folder ID...")
    
    credentials, _ = default(scopes=SCOPES)
    service = build("drive", "v3", credentials=credentials)
    
    PARTY_LOGOS_DIR_PATH = "tmp/cropped-party-logos"
        
    # Read & Save party logos from Google Drive
    read_and_save_images_from_drive(
        service, 
        PARTY_LOGOS_DRIVE_FOLDER_ID, 
        output_dir_path=PARTY_LOGOS_DIR_PATH,
        crop=False  # Don't crop party logos, just save them
    )

    for file in os.listdir(PARTY_LOGOS_DIR_PATH):
        
        # Get party name from file name
        party_name = re.sub(r"\..*$", "", file)  # Remove file extension
        print(f"Updating logo for {party_name}...")
        
        # Update the image URL in Politigraph
        update_party_logo_image_url(
            party_name=party_name, 
            image_url=f"https://politigraph.wevis.info/assets/organizations/political-parties/{file}"
        )
        print(f"Updated logo URL for {party_name} to https://politigraph.wevis.info/assets/organizations/political-parties/{file}")
        
if __name__ == "__main__":
    main()