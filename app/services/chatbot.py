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
                    prev_chat_context=None):
        response = self.client.chat.completions.create(
           messages = [
                        {
                            "role": "system",
                            "content": (
                                f"You are a helpful and concise assistant. Answer the user's queries using only the information provided in the following document:\n\n{context_doc}\n\n"
                                f"Also, take into account the relevant context from the previous conversation:\n\n{prev_chat_context}\n\n"
                                "If the answer cannot be found in the document or prior context, respond with 'I don't have enough information to answer that.'"
                            )
                        },
                        {
                            "role": "user",
                            "content": user_query
                        }
                    ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            model=self.model
        )
        return response.choices[0].message.content
    
    def transform_document(self, document_text: Any, specifactions: Any):
        response = self.client.chat.completions.create(
            messages = [
                        {
                            "role": "system",
                            "content": (
                                f"You are a precise and helpful assistant. Your task is to transform documents strictly based on the following specifications:\n\n{specifactions}\n\n"
                                "Preserve all tables, diagrams, and numerical data exactly as they appear in the original text. Do not alter their formatting or content."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Please transform the document below according to the specifications provided.\n\n"
                                f"Document Text:\n{document_text}"
                            )
                        }
                    ],
            temperature=0.7,
            top_p=1.0,
            model=self.model
        )
        document = response.choices[0].message.content
        return document
    
    def create_session_name(self, final_documnt: Any):
        response = self.client.chat.completions.create(
            messages = [
                            {
                                "role": "system",
                                "content": (
                                    "You are a creative and helpful assistant. Your task is to generate a unique, concise session name (maximum 100 characters) that summarizes or represents the core idea of the provided document."
                                )
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Based on the following document content, generate a unique and meaningful session name:\n\n{final_documnt}"
                                )
                            }
                        ],
            temperature=0.7,
            top_p=1.0,
            model=self.model
        )
        session_name = response.choices[0].message.content.strip()
        return session_name
    
    def keywords_extraction(self, document_text: Any):
        response = self.client.chat.completions.create(
            messages = [
                            {
                                "role": "system",
                                "content": (
                                    "You are a helpful and precise assistant. Your task is to extract the most relevant and meaningful keywords from a given document."
                                    " Focus on nouns, noun phrases, technical terms, and key concepts. Avoid generic or overly common words."
                                )
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Extract the top keywords from the following document text. Present them as a comma-separated list or in bullet points:\n\n{document_text}"
                                )
                            }
                        ],
            max_tokens=150,
            temperature=0.7,
            top_p=1.0,
            model=self.model
        )
        keywords = response.choices[0].message.content.strip()
        return keywords

# if __name__ == "__main__":

#     bot = AzureChatbot()
#     image_url = "https://fra.cloud.appwrite.io/v1/storage/buckets/685d78f0002b38b0ae92/files/685ffb95a39ef5432395/view?project=685d78c7002e37b728f0&mode=admin"
#     reply = bot.image_to_text(public_image_url=image_url)
#     print(reply)