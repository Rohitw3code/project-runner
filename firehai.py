import requests
import socket
from datetime import datetime

firebase_url = 'https://project-runnner-default-rtdb.firebaseio.com/'
hostname = socket.gethostname()
localtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
txt_file_path = 'hello.txt'

try:
    with open(txt_file_path, 'r') as file:
        file_data = file.read()
except FileNotFoundError:
    exit()

data_to_upload = {'runnner': file_data}
db_path = f'users/{hostname}/{localtime}.json'
response = requests.put(firebase_url + db_path, json=data_to_upload)

if response.status_code == 200:
    print('Data written to Firebase successfully!')
else:
    print(f'Failed to write data: {response.status_code}')
