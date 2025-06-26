import os
import requests
from appwrite.client import Client
from appwrite.services.storage import Storage
from config.config import appwrite_api_key, appwrite_endpoint, appwrite_project_id, appwrite_bucket_id
from pdf2image import convert_from_bytes
from urllib.parse import urlparse
from django.utils import timezone
from models import UserSession


class FileTranslator:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(appwrite_endpoint).set_project(appwrite_project_id).set_key(appwrite_api_key)
        self.storage = Storage(self.client)

    def upload_file(self, file_path, remote_filename=None):
        with open(file_path, 'rb') as f:
            result = self.storage.create_file(
                bucket_id=appwrite_bucket_id,
                file_id='unique()',
                file=f,
                name=remote_filename or os.path.basename(file_path),
                permissions=["read(\"*\")"]  # Make file public
            )
        file_id = result["$id"]
        public_url = f"{appwrite_endpoint}/v1/storage/buckets/{appwrite_bucket_id}/files/{file_id}/view?project={appwrite_project_id}"
        return public_url

    def pdf_to_images_and_store(self, pdf_public_url, session_id, output_folder="output"):
        os.makedirs(output_folder, exist_ok=True)

        response = requests.get(pdf_public_url)
        if response.headers.get("Content-Type") != "application/pdf":
            raise ValueError("Invalid content type, expected PDF.")

        pdf_bytes = response.content
        images = convert_from_bytes(pdf_bytes, dpi=300)

        pdf_name = os.path.splitext(os.path.basename(urlparse(pdf_public_url).path))[0]
        public_image_urls = []

        for i, image in enumerate(images):
            filename = f"{pdf_name}_page_{i+1}.jpg"
            filepath = os.path.join(output_folder, filename)
            image.save(filepath, "JPEG")

            public_url = self.upload_file(filepath, remote_filename=filename)
            public_image_urls.append(public_url)

        # Save public URLs to UserSession model
        session = UserSession.objects.get(id=session_id)
        session.pdf_image_urls = str(public_image_urls)  # or use json.dumps if preferred
        session.last_activity = timezone.now()
        session.save()

        return public_image_urls
