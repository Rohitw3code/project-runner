import os
import requests

# Your ImgBB API key
api_key = 'de7994d6d49af160676a69e6c10e3026'

# Path to the folder containing images
folder_path = 'ss'

# API endpoint for ImgBB upload
url = 'https://api.imgbb.com/1/upload'

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    # Check if it's an image file
    if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        with open(file_path, 'rb') as image_file:
            # Prepare the data for the request
            files = {'image': image_file}
            params = {'key': api_key}

            # Make the POST request to upload the image
            response = requests.post(url, files=files, params=params)

        # Handle the response
        if response.status_code == 200:
            response_json = response.json()
            image_url = response_json['data']['url']
            print(f"Uploaded {filename} to ImgBB. URL: {image_url}")
        else:
            print(f"Failed to upload {filename}. Response: {response.text}")
