import os
import requests
import base64
from openai import AzureOpenAI
from config.config import azure_chatbot_access_key, azure_chatbot_endpoint, azure_chatbot_deployment_name, azure_chatbot_api_version
from typing import Any

class AzureChatbot:
    def __init__(self):
        self.endpoint = f"{azure_chatbot_endpoint}"
        self.subscription_key = f"{azure_chatbot_access_key}"
        self.api_version = f"{azure_chatbot_api_version}"
        self.model = f'{azure_chatbot_deployment_name}'
        self.client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.subscription_key,
        )

    def image_to_text(self, public_image_url: str = None):
        if not public_image_url:
            raise ValueError("Public image URL must be provided.")
        
        img_byte = requests.get(public_image_url).content
        img_base64 = base64.b64encode(img_byte).decode("utf-8")

        strict_prompt = (
            "Analyze this handwritten notebook image. "
            "Only describe visible and clearly verifiable elements: text, formulas, equations, tables. "
            "If any diagram or graph is NOT explicitly shown, do NOT mention it. "
            "Avoid making assumptions. Do not organize the content into 'Left Page' and 'Right Page' structure if applicable. "
            "Preserve mathematical formatting and table structure accurately."
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": strict_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2048,
            temperature=0.3,
            top_p=1.0,
        )
        return response.choices[0].message.content
        

    def rag_chatbot(self, user_query: str, context_doc: Any,
                    max_tokens: int = 4096, temperature: float = 1.0, top_p: float = 1.0,
                    vector_embeddings=None):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are a helpful assistant which only provides information from {context_doc} if not provide raise the issue."},
                {"role": "user", "content": user_query}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            model=self.model
        )
        return response.choices[0].message.content
    
    def transform_document(self, document_text: Any, specifactions: Any):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are a helpful assistant that transforms documents according to the provided specification {specifactions}."},
                {"role": "user", "content": f"Transform the following document text according to the specifications: {specifactions}\n\nDocument Text: {document_text} leave the tanle and diagram as it is and also the numericals"}
            ],
            temperature=0.7,
            top_p=1.0,
            model=self.model
        )
        document = response.choices[0].message.content
        return document
    
    def create_session_name(self, final_documnt: Any):
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates unique session names."},
                {"role": "user", "content": f"Generate a unique session name for a user session based on the following document: {final_documnt}"}
            ],
            temperature=0.7,
            top_p=1.0,
            model=self.model
        )
        session_name = response.choices[0].message.content.strip()
        return session_name

# if __name__ == "__main__":

#     bot = AzureChatbot()
#     image_url = "https://fra.cloud.appwrite.io/v1/storage/buckets/685d78f0002b38b0ae92/files/685ffb95a39ef5432395/view?project=685d78c7002e37b728f0&mode=admin"
#     reply = bot.image_to_text(public_image_url=image_url)
#     print(reply)