import os
import time
import json
import shutil
import uuid
from datetime import datetime
import requests

# Path to the folder that the host will mount
WATCH_FOLDER = '/mnt/target-folder'  # Mounted directory in Docker
STORAGE_FOLDER = '/storage'
CLAMAV_SERVER_URL = 'http://clamav:3310/scan'  # URL to ClamAV container's scanning endpoint

# Ensure the storage folder exists inside the container
os.makedirs(STORAGE_FOLDER, exist_ok=True)

# Function to create the metadata JSON
def create_metadata(file_path):
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "type": os.path.splitext(file_path)[1],  # file extension as type
        "host_path": file_path,
        "status": "moved"
    }

# Function to handle the file processing
def process_file(file_path):
    # Move the original file to the container's /storage folder
    destination = os.path.join(STORAGE_FOLDER, os.path.basename(file_path))
    shutil.move(file_path, destination)
    print(f"File moved to storage: {destination}")

    # Create metadata for the file
    metadata = create_metadata(file_path)
    metadata_file = f"{destination}.metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)

    print(f"Metadata created: {metadata_file}")

    # Notify ClamAV container for scanning
    notify_clamav(destination, metadata_file)

# Function to notify the ClamAV container
def notify_clamav(file_path, metadata_file):
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(CLAMAV_SERVER_URL, files={'file': file})
        
        if response.status_code == 200:
            print(f"ClamAV scan successful for: {file_path}")
            update_metadata(metadata_file, "scanned", response.json())
        else:
            print(f"ClamAV scan error ({response.status_code}): {response.text}")
            update_metadata(metadata_file, "scan_failed", {"error": response.text})
    except Exception as e:
        print(f"Error notifying ClamAV: {e}")
        update_metadata(metadata_file, "scan_failed", {"error": str(e)})

# Function to update metadata after ClamAV scan
def update_metadata(metadata_file, status, clamav_result):
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    metadata["status"] = status
    metadata["clamav_result"] = clamav_result

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata updated: {metadata_file}")

# Watch for new files in the target folder using polling
def watch_directory():
    print(f"Watching directory: {WATCH_FOLDER}")
    processed_files = set()  # To keep track of processed files

    while True:
        # List files in the directory
        for file_name in os.listdir(WATCH_FOLDER):
            file_path = os.path.join(WATCH_FOLDER, file_name)
            # Skip directories and already processed files
            if os.path.isdir(file_path) or file_name in processed_files:
                continue

            print(f"New file detected: {file_path}")
            process_file(file_path)
            processed_files.add(file_name)

        # Sleep for 5 seconds before checking again
        time.sleep(5)

# Start watching
if __name__ == '__main__':
    watch_directory()
