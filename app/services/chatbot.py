import os
from openai import AzureOpenAI
from config.config import azure_chatbot_access_key, azure_chatbot_endpoint, azure_chatbot_deployment_name, azure_chatbot_api_version
from typing import Any

class AzureChatbot:
    def __init__(self):
        self.endpoint = azure_chatbot_endpoint
        self.subscription_key = azure_chatbot_access_key
        self.api_version = azure_chatbot_api_version
        self.model = azure_chatbot_deployment_name
        self.client = AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            api_key=self.subscription_key,
        )

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
                {"role": "user", "content": f"Transform the following document text according to the specifications: {specifactions}\n\nDocument Text: {document_text}"}
            ],
            temperature=0.7,
            top_p=1.0,
            model=self.model
        )
        document = response.choices[0].message.content
        return document

# if __name__ == "__main__":

#     bot = AzureChatbot()
#     messages = "Tell me about the fastest Ferrari ever made."
#     reply = bot.rag_chatbot(messages)
#     print(reply)