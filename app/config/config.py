import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

django_secret_key = os.getenv("DJANGO_SECRET_KEY")
azure_chatbot_endpoint = os.getenv("AZURE_AI_CHATBOT_ENDPOINT")
azure_chatbot_access_key = os.getenv("AZURE_AI_CHATBOT_KEY")
azure_chatbot_deployment_name = os.getenv("AZURE_AI_CHATBOT_DEPLOYMENT_NAME")
azure_chatbot_api_version = os.getenv("AZURE_API_VERSION")
appwrite_api_key = os.getenv("APPWRITE_API_KEY")
appwrite_endpoint = os.getenv("APPWRITE_ENDPOINT")
appwrite_project_id = os.getenv("APPWRITE_PROJECT_ID")
appwrite_bucket_id = os.getenv("APPWRITE_BUCKET_ID")
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))
