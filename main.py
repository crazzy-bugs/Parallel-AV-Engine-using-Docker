import os
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

# Configuration
TARGET_FOLDER = "C:/Users/SARTHAK/Desktop/sih-2024/python-server/target_folder"  # Folder to watch
FILE_STORAGE = "C:/Users/SARTHAK/Desktop/sih-2024/python-server/file_storage"    # Folder to move detected files
MANAGEMENT_SERVER_URL = "http://management-server:5000/process_file"  # Docker Compose service name

class FileWatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            print(f"New file detected: {file_path}")
            try:
                self.process_new_file(file_path)
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    def process_new_file(self, file_path):
        if not os.path.exists(FILE_STORAGE):
            os.makedirs(FILE_STORAGE)  # Ensure the file storage directory exists
        
        file_name = os.path.basename(file_path)
        destination_path = os.path.join(FILE_STORAGE, file_name)
        
        try:
            shutil.move(file_path, destination_path)
            print(f"File moved to storage: {destination_path}")
            self.notify_management_server(destination_path)
        except Exception as e:
            print(f"Error moving file {file_path} to storage: {e}")

    def notify_management_server(self, file_path):
        data = {"file_path": file_path}
        try:
            response = requests.post(MANAGEMENT_SERVER_URL, json=data)
            if response.status_code == 200:
                print(f"File successfully sent to management server: {file_path}")
            else:
                print(f"Error from management server: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"Failed to connect to management server: {e}")

def start_file_watcher():
    if not os.path.exists(TARGET_FOLDER):
        print(f"Error: Target folder {TARGET_FOLDER} does not exist.")
        return

    event_handler = FileWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path=TARGET_FOLDER, recursive=False)
    
    # Use polling for cross-platform compatibility (especially for Windows)
    if os.name == 'nt':  # For Windows systems
        observer.start(polling=True)
    else:
        observer.start()

    print(f"Watching folder: {TARGET_FOLDER}")
    
    try:
        observer.join()  # Wait for the observer to finish
    except KeyboardInterrupt:
        observer.stop()
        print("File watcher stopped.")

if __name__ == "__main__":
    start_file_watcher()
