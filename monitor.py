import os
import re
import time
import json
import shutil
import uuid
from datetime import datetime
import requests
import subprocess
import hashlib

# Path configurations
WATCH_FOLDER = '/mnt/target-folder'  # This is where files will be watched
STORAGE_FOLDER = '/storage'  # This is where files will be moved and scanned
DUMMY_FOLDER = '/mnt/dummy-folder'  # Dummy folder to show placeholder during scanning
ORIGINAL_PATHS_FILE = '/tmp/original_paths.json'  # Tracks original file and folder paths
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
    {
        "name": "windows-defender",
        "type": "network",
        "url": "http://windows-defender:3993/scan",
        "method": "network_scan"
    },
    {
        "name": "fprot",
        "type": "network",
        "url": "http://fprot:3993/scan",
        "method": "network_scan"
    }
]

# Ensure the storage folder exists
os.makedirs(STORAGE_FOLDER, exist_ok=True)
os.makedirs(DUMMY_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(ORIGINAL_PATHS_FILE), exist_ok=True)

def load_original_paths():
    """Load original file and folder paths from a JSON file."""
    try:
        with open(ORIGINAL_PATHS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_original_paths(paths_dict):
    """Save original file and folder paths to a JSON file."""
    with open(ORIGINAL_PATHS_FILE, 'w') as f:
        json.dump(paths_dict, f, indent=4)

def generate_file_hash(file_path, chunk_size=65536):
    """
    Generate a hash for a file with minimal memory usage.
    Useful for large files.
    """
    if os.path.isdir(file_path):
        # For directories, generate a hash of all file contents
        hasher = hashlib.sha256()
        for root, _, files in os.walk(file_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'rb') as f:
                        for chunk in iter(lambda: f.read(chunk_size), b''):
                            hasher.update(chunk)
                except Exception:
                    pass  # Skip files that can't be read
        return hasher.hexdigest()
    
    # For files, use existing hash method
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_dummy_placeholder(original_path):
    """
    Create a dummy file or folder to maintain visibility during scanning.
    """
    # Generate a unique dummy name
    dummy_name = f"scanning_{uuid.uuid4()}_{os.path.basename(original_path)}"
    dummy_path = os.path.join(DUMMY_FOLDER, dummy_name)
    
    if os.path.isdir(original_path):
        # Create dummy folder
        os.makedirs(dummy_path, exist_ok=True)
    else:
        # Create dummy file with size information
        with open(dummy_path, 'w') as f:
            f.write(f"Scanning in progress...\n")
            f.write(f"Original file: {original_path}\n")
            f.write(f"Size: {os.path.getsize(original_path)} bytes")
    
    return dummy_path

def scan_with_clamdscan(path):
    """
    Scan file or directory using clamdscan with optimized error handling.
    """
    try:
        result = subprocess.run(
            ['clamdscan', '--fdpass', path], 
            capture_output=True, 
            text=True,
            timeout=600  # 10-minute timeout for large folders
        )

        structured_result = {
            "status": "clean",
            "details": {
                "engine": "ClamAV",
                "result": "No threats found",
                "updated": datetime.now().strftime("%Y%m%d")
            }
        }

        if result.returncode == 1:
            structured_result["status"] = "infected"
            infected_match = re.search(r":\s(.*)\sFOUND", result.stdout)
            structured_result["details"]["result"] = (
                infected_match.group(1) if infected_match else "Unknown threat"
            )
        elif result.returncode > 1:
            structured_result = {
                "status": "error",
                "details": {
                    "engine": "ClamAV",
                    "result": "Scanning error",
                    "extra": result.stderr
                }
            }

        return structured_result

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "details": {
                "engine": "ClamAV",
                "result": "Scanning timed out",
                "extra": "File/Folder may be too large"
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "details": {
                "engine": "ClamAV",
                "result": "Exception during scanning",
                "extra": str(e)
            }
        }
def comodo(file_path):
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

def fprot(file_path):
    try:
        url = "http://fprot:3993/scan"
        with open(file_path, 'rb') as file:
            files = {'malware': file}
            response = requests.post(url, files=files, timeout=30)

        if response.status_code == 200:
            return {"status": "clean", "details": response.json()}
        else:
            return {"status": "error", "details": response.text}
    except Exception as e:
        return {"status": "error", "details": str(e)}

def windows_defender(file_path):
    try:
        url = "http://windows-defender:3993/scan"
        with open(file_path, 'rb') as file:
            files = {'malware': file}
            response = requests.post(url, files=files, timeout=30)

        if response.status_code == 200:
            return {"status": "clean", "details": response.json()}
        else:
            return {"status": "error", "details": response.text}
    except Exception as e:
        return {"status": "error", "details": str(e)}

def escan(file_path):
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

def process_item(item_path):
    """
    Process a file or folder for scanning.
    """
    # Track original paths
    original_paths = load_original_paths()
    
    # If it's a directory, process each file in the directory
    if os.path.isdir(item_path):
        for root, _, files in os.walk(item_path):
            for file in files:
                file_path = os.path.join(root, file)
                process_file(file_path)
    else:
        # If it's a single file, process it
        process_file(item_path)

def mcafee(file_path):
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
    """Process individual files (whether inside a directory or standalone)"""
    original_paths = load_original_paths()
    
    # Generate unique name to prevent conflicts
    unique_name = f"{datetime.now().timestamp()}_{os.path.basename(file_path)}"
    destination = os.path.join(STORAGE_FOLDER, unique_name)
    
    try:
        # Create dummy placeholder
        dummy_path = create_dummy_placeholder(file_path)
        
        # Move file to storage
        shutil.move(file_path, destination)
        
        # Store original path
        original_paths[unique_name] = os.path.abspath(file_path)
        save_original_paths(original_paths)
        
        # Perform scanning with all AV engines
        clamdscan_result = scan_with_clamdscan(destination)
        escan_result = escan(destination)
        mcafee_result = mcafee(destination)
        comodo_result = comodo(destination)
        windows_defender_result = windows_defender(destination)
        fprot_result = fprot(destination)
        
        # Create metadata
        metadata = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": "file",
            "host_path": os.path.abspath(destination),
            "original_path": original_paths[unique_name],
            "file_hash": generate_file_hash(destination),
            "status": "scanned",
            "av_results": {
                "clamdscan": clamdscan_result,
                "escan": escan_result,
                "mcafee": mcafee_result,
                "comodo": comodo_result,
                "windows-defender": windows_defender_result,
                "fprot": fprot_result
            }
        }
        
        # Write metadata
        metadata_file = f"{destination}.metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        # Restoration logic
        if all(result["status"] == "clean" for result in metadata["av_results"].values()):
            # Remove dummy placeholder
            if os.path.exists(dummy_path):
                if os.path.isdir(dummy_path):
                    shutil.rmtree(dummy_path)
                else:
                    os.remove(dummy_path)
            
            # Restore file to original location
            shutil.move(destination, original_paths[unique_name])
            
            # Remove path tracking
            del original_paths[unique_name]
            save_original_paths(original_paths)
            
            print(f"File restored to original location: {original_paths[unique_name]}")
            return True
        else:
            print(f"Infected file quarantined: {destination}")
            return False
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        # Fallback: return file to original location in case of error
        if os.path.exists(destination):
            try:
                shutil.move(destination, original_paths.get(unique_name, file_path))
            except Exception as fallback_error:
                print(f"Fallback restoration failed: {fallback_error}")
        return False
    """Process individual files (whether inside a directory or standalone)"""
    original_paths = load_original_paths()
    
    # Generate unique name to prevent conflicts
    unique_name = f"{datetime.now().timestamp()}_{os.path.basename(file_path)}"
    destination = os.path.join(STORAGE_FOLDER, unique_name)
    
    try:
        # Create dummy placeholder
        dummy_path = create_dummy_placeholder(file_path)
        
        # Move file to storage
        shutil.move(file_path, destination)
        
        # Store original path
        original_paths[unique_name] = os.path.abspath(file_path)
        save_original_paths(original_paths)
        
        # Perform scanning
        clamdscan_result = scan_with_clamdscan(destination)
        
        # Create metadata
        metadata = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": "file",
            "host_path": os.path.abspath(destination),
            "original_path": original_paths[unique_name],
            "file_hash": generate_file_hash(destination),
            "status": "scanned",
            "av_results": {
                "clamdscan": {
                    "status": clamdscan_result["status"],
                    "details": clamdscan_result["details"]
                }
            }
        }
        
        # Write metadata
        metadata_file = f"{destination}.metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        # Restoration logic
        if clamdscan_result["status"] == "clean":
            # Remove dummy placeholder
            if os.path.exists(dummy_path):
                if os.path.isdir(dummy_path):
                    shutil.rmtree(dummy_path)
                else:
                    os.remove(dummy_path)
            
            # Restore file to original location
            shutil.move(destination, original_paths[unique_name])
            
            # Remove path tracking
            del original_paths[unique_name]
            save_original_paths(original_paths)
            
            print(f"File restored to original location: {original_paths[unique_name]}")
            return True
        else:
            print(f"Infected file quarantined: {destination}")
            return False
    
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        # Fallback: return file to original location in case of error
        if os.path.exists(destination):
            try:
                shutil.move(destination, original_paths.get(unique_name, file_path))
            except Exception as fallback_error:
                print(f"Fallback restoration failed: {fallback_error}")
        return False

def watch_directory():
    """
    Watch directory for new files and folders.
    """
    print(f"Watching directory: {WATCH_FOLDER}")
    processed_items = set()

    while True:
        try:
            for item_name in os.listdir(WATCH_FOLDER):
                item_path = os.path.join(WATCH_FOLDER, item_name)
                
                # Skip already processed items
                if item_name in processed_items:
                    continue
                
                # Process file or folder
                print(f"Processing item: {item_path}")
                process_item(item_path)
                processed_items.add(item_name)
            
            # Efficient sleep to prevent high CPU usage
            time.sleep(5)
        
        except Exception as e:
            print(f"Error in watch_directory: {e}")
            time.sleep(10)  # Longer sleep on persistent errors

if __name__ == '__main__':
    watch_directory()
