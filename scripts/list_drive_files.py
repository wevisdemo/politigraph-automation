from google.auth import default
from googleapiclient.discovery import build
import os

google_drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

def list_files_in_drive_folder(folder_id):
    """Lists file names in a given Google Drive folder."""
    credentials, _ = default()
    service = build("drive", "v3", credentials=credentials)

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(name)").execute()
    files = results.get('files', [])

    if not files:
        print("No files found in the folder.")
    else:
        print("Files in folder:")
        for file in files:
            print(file['name'])

if __name__ == "__main__":
    list_files_in_drive_folder(google_drive_folder_id)
