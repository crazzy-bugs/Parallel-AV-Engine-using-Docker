import os
import time
import json
import shutil
import uuid
from datetime import datetime
import requests
import subprocess

# Path configurations
WATCH_FOLDER = '/mnt/target-folder'
STORAGE_FOLDER = '/storage'

# Antivirus configuration
ANTIVIRUS_CONFIGS = [
    {
        "name": "clamav",
        "type": "network",
        "url": "http://clamav:3310/scan",
        "method": "network_scan"
    },
    {
        "name": "escan",
        "type": "network",  # Use network as eScan is running as a web service
        "url": "http://escan:3993/scan",  # Adjusted URL to use exposed port
        "method": "network_scan"
    }
]

# Ensure the storage folder exists
os.makedirs(STORAGE_FOLDER, exist_ok=True)

def create_metadata(file_path):
    absolute_path = os.path.abspath(file_path)  # Convert to absolute path
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "type": os.path.splitext(file_path)[1],
        "host_path": absolute_path,  # Store absolute path
        "status": "moved"
    }

def network_scan_clamav(file_path):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            response = requests.post("http://clamav:3310/scan", files=files, timeout=30)

        if response.status_code == 200:
            return {"status": "clean", "details": response.json()}
        else:
            return {"status": "error", "details": response.text}
    except Exception as e:
        return {"status": "error", "details": str(e)}

def local_scan_escan(file_path):
    try:
        # eScan expects a file POST to the /scan endpoint
        url = "http://escan:3993/scan"  # Adjusted URL
        with open(file_path, 'rb') as file:
            files = {'malware': file}
            response = requests.post(url, files=files, timeout=30)

        if response.status_code == 200:
            return {"status": "clean", "details": response.json()}
        else:
            return {"status": "error", "details": response.text}
    except Exception as e:
        return {"status": "error", "details": str(e)}

def process_file(file_path):
    # Move file to storage with absolute path
    destination = os.path.join(STORAGE_FOLDER, os.path.basename(file_path))
    shutil.move(file_path, destination)
    print(f"File moved to storage: {destination}")

    # Create metadata with the absolute path
    metadata = create_metadata(destination)  # Use the new location for metadata
    metadata_file = f"{destination}.metadata.json"

    # Scan with multiple AVs
    scan_results = {}
    for av_config in ANTIVIRUS_CONFIGS:
        try:
            if av_config["method"] == "network_scan":
                if av_config["name"] == "clamav":
                    scan_result = network_scan_clamav(destination)
                elif av_config["name"] == "escan":
                    scan_result = local_scan_escan(destination)
            else:
                scan_result = {"status": "unsupported", "details": "Unknown scan method"}

            scan_results[av_config["name"]] = scan_result
        except Exception as e:
            scan_results[av_config["name"]] = {
                "status": "error",
                "details": str(e)
            }

    # Update metadata with scan results
    metadata["status"] = "scanned"
    metadata["av_results"] = scan_results

    # Write metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata created: {metadata_file}")

def watch_directory():
    print(f"Watching directory: {WATCH_FOLDER}")
    processed_files = set()

    while True:
        for file_name in os.listdir(WATCH_FOLDER):
            file_path = os.path.join(WATCH_FOLDER, file_name)
            if os.path.isdir(file_path) or file_name in processed_files:
                continue

            print(f"New file detected: {file_path}")
            process_file(file_path)
            processed_files.add(file_name)

        time.sleep(5)

if __name__ == '__main__':
    watch_directory()
