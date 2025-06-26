import os
import requests
from appwrite.client import Client
from appwrite.services.storage import Storage
from config.config import appwrite_api_key, appwrite_endpoint, appwrite_project_id, appwrite_bucket_id
from pdf2image import convert_from_bytes
from urllib.parse import urlparse


class FileTranslator:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(appwrite_endpoint).set_project(appwrite_project_id).set_key(appwrite_api_key)
        self.storage = Storage(self.client)

    def upload_file(self, file_path, remote_filename=None):
        """Uploads a file to Appwrite storage."""
        with open(file_path, 'rb') as f:
            return self.storage.create_file(
                bucket_id=appwrite_bucket_id,
                file_id='unique()',
                file=f,
                name=remote_filename or os.path.basename(file_path)
            )

    def pdf_to_images(self, pdf_public_url, output_folder="output"):
        """Converts a public PDF URL to images and uploads them to Appwrite."""
        os.makedirs(output_folder, exist_ok=True)

        # Get PDF bytes from Appwrite public link
        response = requests.get(pdf_public_url)
        if response.headers.get("Content-Type") != "application/pdf":
            raise ValueError("Invalid content type, expected PDF.")

        pdf_bytes = response.content
        images = convert_from_bytes(pdf_bytes, dpi=300)

        # Get a clean name to group images (like a folder prefix)
        pdf_name = os.path.splitext(os.path.basename(urlparse(pdf_public_url).path))[0]

        uploaded_files = []
        for i, image in enumerate(images):
            filename = f"{pdf_name}_page_{i+1}.jpg"
            filepath = os.path.join(output_folder, filename)
            image.save(filepath, "JPEG")

            # Upload to Appwrite
            uploaded_file = self.upload_file(filepath, remote_filename=filename)
            uploaded_files.append(uploaded_file)

        return uploaded_files


# if __name__ == "__main__":
#     url = "https://fra.cloud.appwrite.io/v1/storage/buckets/685d16e20006d61d0d65/files/685d16fd000488dbe536/view?project=685d16b5002d401cbf0c&mode=admin"

#     translator = FileTranslator()
#     results = translator.pdf_to_images(url)
#     for result in results:
#         print("Uploaded:", result["$id"], result["name"])
