import os
import requests
from appwrite.client import Client
from appwrite.input_file import InputFile
from appwrite.services.storage import Storage
from config.config import appwrite_api_key, appwrite_endpoint, appwrite_project_id, appwrite_bucket_id
from pdf2image import convert_from_bytes
from urllib.parse import urlparse
from io import BytesIO


class FileTranslator:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(appwrite_endpoint).set_project(appwrite_project_id).set_key(appwrite_api_key)
        self.storage = Storage(self.client)

    def upload_file(self, file_path, remote_filename=None):
        input_file = InputFile.from_path(file_path)  # ✅ fix
        result = self.storage.create_file(
            bucket_id=appwrite_bucket_id,
            file_id='unique()',
            file=input_file
        )
        file_id = result["$id"]
        public_url = f"{appwrite_endpoint}/storage/buckets/{appwrite_bucket_id}/files/{file_id}/view?project={appwrite_project_id}"
        return public_url

    def pdf_to_images_and_store(self, pdf_public_url):
        response = requests.get(pdf_public_url)
        if response.headers.get("Content-Type") != "application/pdf":
            raise ValueError("Invalid content type, expected PDF.")

        pdf_bytes = response.content
        images = convert_from_bytes(pdf_bytes, dpi=300)

        pdf_name = os.path.splitext(os.path.basename(urlparse(pdf_public_url).path))[0]
        public_image_urls = []

        for i, image in enumerate(images):
            filename = f"{pdf_name}_page_{i+1}.jpg"

            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)

            input_file = InputFile.from_bytes(buffer.read(), filename=filename)
            result = self.storage.create_file(
                bucket_id=appwrite_bucket_id,
                file_id='unique()',
                file=input_file
            )
            file_id = result["$id"]
            public_url = f"{appwrite_endpoint}/storage/buckets/{appwrite_bucket_id}/files/{file_id}/view?project={appwrite_project_id}"
            public_image_urls.append(public_url)

        print(public_image_urls)
        return public_image_urls