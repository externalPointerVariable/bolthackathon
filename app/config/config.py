import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

azure_chatbot_endpoint = os.getenv("AZURE_AI_CHATBOT_ENDPOINT")
azure_chatbot_access_key = os.getenv("AZURE_AI_CHATBOT_KEY")
azure_chatbot_deployment_name = os.getenv("AZURE_API_VERSION")
azure_chatbot_api_version = os.getenv("AZURE_API_VERSION")
azure_ocr_endpoint = os.getenv("AZURE_OCR_ENDPOINT")
azure_ocr_access_key = os.getenv("AZURE_OCR_KEY")