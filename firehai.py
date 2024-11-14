import requests
import socket
from datetime import datetime

# Your Firebase Realtime Database URL (without the trailing slash)
firebase_url = 'https://project-runnner-default-rtdb.firebaseio.com/'

# Get the hostname of the machine
hostname = socket.gethostname()

# Get the current local time
localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Define the path to the text file
txt_file_path = 'testdrop.py'

# Read the content of the text file
try:
    with open(txt_file_path, 'r') as file:
        file_data = file.read()
except FileNotFoundError:
    print(f"Error: The file '{txt_file_path}' was not found.")
    exit()

# Prepare the data to send to Firebase
data_to_upload = {
    'runnner': file_data
}

# Define the path in the database: users -> hostname -> localtime -> data
db_path = f'users/{hostname}/{localtime}.json'

# Send a PUT request to write data to Firebase
response = requests.put(firebase_url + db_path, json=data_to_upload)

# Check the response from Firebase
if response.status_code == 200:
    print('Data written to Firebase successfully!')
else:
    print(f'Failed to write data: {response.status_code} - {response.text}')
