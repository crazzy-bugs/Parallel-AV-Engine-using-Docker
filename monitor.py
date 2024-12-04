import os
import re
import time
import json
import shutil
import uuid
from datetime import datetime
import requests
import subprocess
# import pyclamd

# Path configurations
WATCH_FOLDER = '/mnt/target-folder'  # This is where files will be watched
STORAGE_FOLDER = '/storage'  # This is where files will be moved and scanned

# Antivirus configuration
ANTIVIRUS_CONFIGS = [
    # {
    #     "name": "clamav",
    #     "type": "network",
    #     "url": "http://clamav:3310/scan",
    #     "method": "network_scan"
    # },
    {
        "name":"clamav",
        "type":"local",
        "url":"http://clamav:3310/scan",
        "method":"local_scan"
    },
    {
        "name": "escan",
        "type": "network",
        "url": "http://escan:3993/scan",
        "method": "network_scan"
    },
    {
        "name": "mcafee",
        "type": "network",
        "url": "http://mcafee:3993/scan",
        "method": "network_scan"
    },
    {
        "name": "comodo",
        "type": "network",
        "url": "http://comodo:3993/scan",
        "method": "network_scan"
    },
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

def scan_with_clamdscan(folder_path):
    """
    Scan the entire storage folder using clamdscan and return structured results.
    """
    try:
        # Run clamdscan on the storage folder
        result = subprocess.run(
            ['clamdscan', '-r', '--fdpass', folder_path], 
            capture_output=True, 
            text=True
        )

        # Initialize structured output
        structured_result = {
            "status": "clean",  # Default assumption
            "details": {
                "engine": "ClamAV",
                "result": "No threats found",
                "updated": datetime.now().strftime("%Y%m%d")  # Simulated last update date
            }
        }

        # Parse the raw output
        if result.returncode == 0:
            # No infections found
            structured_result["status"] = "clean"
        elif result.returncode == 1:
            # Infections found, parse the output
            infected_match = re.search(r":\s(.*)\sFOUND", result.stdout)
            if infected_match:
                structured_result["status"] = "infected"
                structured_result["details"]["result"] = infected_match.group(1)  # Extract malware name
            else:
                structured_result["status"] = "infected"
                structured_result["details"]["result"] = "Unknown threat detected"  # Fallback for unmatched output
        else:
            # Scanning error
            structured_result["status"] = "error"
            structured_result["details"]["result"] = "Error in scanning"
            structured_result["details"]["extra"] = result.stderr  # Include error details

        return structured_result

    except Exception as e:
        # Return error details in case of exceptions
        return {
            "status": "error",
            "details": {
                "engine": "ClamAV",
                "result": "Exception occurred during scanning",
                "extra": str(e)
            }
        }
def network_scan_comodo(file_path):
    try:
        url = "http://comodo:3993/scan"
        with open(file_path, 'rb') as file:
            files = {'malware': file}
            response = requests.post(url, files=files, timeout=30)

        if response.status_code == 200:
            return {"status": "clean", "details": response.json()}
        else:
            return {"status": "error", "details": response.text}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# def scan_with_clamav(file_path):
#     try:
#         # Retry connection to ClamAV until it's ready
#         cd = None
#         retries = 0
#         while retries < 5:
#             try:
#                 cd = pyclamd.ClamdNetworkSocket(host='clamav', port=3310)
#                 if cd.ping():
#                     break  # If ClamAV is responsive, break the retry loop
#             except Exception as e:
#                 retries += 1
#                 print(f"Retrying ClamAV connection ({retries}/5)...")
#                 time.sleep(2)  # Wait before retrying

#         if cd is None or not cd.ping():
#             return {"status": "error", "details": "ClamAV daemon not responding after retries"}

#         # Proceed with scanning once ClamAV is ready
#         scan_result = cd.scan_file(file_path)
#         while scan_result is None:  # If scan is still running, wait and retry
#             print(f"Waiting for ClamAV to finish scanning {file_path}...")
#             time.sleep(1)  # Wait a moment before checking again
#             scan_result = cd.scan_file(file_path)

#         if scan_result:
#             return {"status": "infected", "details": scan_result}
#         else:
#             return {"status": "clean", "details": "No threats found"}
#     except Exception as e:
#         return {"status": "error", "details": str(e)}

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

def network_scan_mcafee(file_path):
    try:
        url = "http://mcafee:3993/scan"
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
    # Move file to storage folder
    destination = os.path.join(STORAGE_FOLDER, os.path.basename(file_path))
    shutil.move(file_path, destination)
    print(f"File moved to storage: {destination}")
    
    # Scan with multiple AVs after moving the file to storage
    scan_results = {}
    for av_config in ANTIVIRUS_CONFIGS:
        try:
            if av_config["method"] == "network_scan":
                if av_config["name"] == "comodo":
                    scan_result = network_scan_comodo(destination)
                elif av_config["name"] == "escan":
                    scan_result = local_scan_escan(destination)
                elif av_config["name"] == "mcafee":
                    scan_result = network_scan_mcafee(destination)
            else:
                scan_result = {"status": "unsupported", "details": "Unknown scan method"}

            scan_results[av_config["name"]] = scan_result
        except Exception as e:
            scan_results[av_config["name"]] = {
                "status": "error",
                "details": str(e)
            }

    # Remove "clamav" key from scan results if present
    scan_results.pop("clamav", None)

    # Create metadata with the scan results
    metadata = create_metadata(destination)
    metadata["status"] = "scanned"
    metadata["av_results"] = scan_results

    # Write metadata
    metadata_file = f"{destination}.metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata created: {metadata_file}")

    # Run clamdscan on the file and append results to its metadata file
    clamdscan_results = scan_with_clamdscan(destination)
    # Standardize the structure for clamdscan
    clamdscan_structured = {
        "status": clamdscan_results["status"],
        "details": {
            "engine": clamdscan_results["details"]["engine"],
            "infected": clamdscan_results["status"] == "infected",
            "result": clamdscan_results["details"]["result"],
            "updated": clamdscan_results["details"]["updated"]
        }
    }

    with open(metadata_file, 'r+') as f:
        metadata = json.load(f)
        metadata["av_results"]["clamdscan"] = clamdscan_structured
        f.seek(0)
        json.dump(metadata, f, indent=4)
        f.truncate()
    print(f"Clamdscan results appended to metadata: {metadata_file}")

def watch_directory():
    print(f"Watching directory: {WATCH_FOLDER}")
    processed_files = set()

    while True:
        for file_name in os.listdir(WATCH_FOLDER):
            file_path = os.path.join(WATCH_FOLDER, file_name)
            if os.path.isdir(file_path) or file_name in processed_files:
                continue

            print(f"New file detected: {file_path}")
            # Move the file to storage and start scanning
            process_file(file_path)
            processed_files.add(file_name)

        time.sleep(5)  # Added back the sleep to prevent high CPU usage

if __name__ == '__main__':
    watch_directory()
