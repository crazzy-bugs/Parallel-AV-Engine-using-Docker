import os
import time
import json
import shutil
import uuid
from datetime import datetime

# Path to the folder that the host will mount
WATCH_FOLDER = '/mnt/target-folder'  # Mounted directory in Docker
STORAGE_FOLDER = '/storage'

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
    # Generate dummy file in the same directory as the original file
    dummy_file = f"{file_path}.dummy"
    with open(dummy_file, 'w') as f:
        f.write('This is a dummy file\n')
    
    # Create metadata for the file
    metadata = create_metadata(file_path)

    # Move the original file to the container's /storage folder
    destination = os.path.join(STORAGE_FOLDER, os.path.basename(file_path))
    shutil.move(file_path, destination)

    # Save metadata as a JSON file with the same name as the original file
    metadata_file = f"{destination}.metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)

    print(f"Processed {file_path} -> Dummy created and file moved.")

# Watch for new files in the target folder
def watch_directory():
    print(f"Watching directory: {WATCH_FOLDER}")
    while True:
        # Use inotifywait to wait for a new file
        for event in os.popen(f'inotifywait -e create --format "%f" {WATCH_FOLDER}'):
            new_file = os.path.join(WATCH_FOLDER, event.strip())
            if os.path.isfile(new_file):
                process_file(new_file)

# Start watching
if __name__ == '__main__':
    watch_directory()
