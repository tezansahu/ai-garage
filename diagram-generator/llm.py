import os
import requests
from dotenv import load_dotenv

class AzureOpenAI:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION')

        self.headers = {
            'Content-Type': 'application/json',
            "api-key": self.api_key,
        }

        self.endpoint = f'{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}'

        self.payload = {
            "messages": [],
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }

    def send_message(self, message, **kwargs):
        if isinstance(message, str):
            self.payload["messages"] = [{"role": "user", "content": message}]
        elif isinstance(message, list) and all(isinstance(item, dict) for item in message):
            self.payload["messages"] = message
        else:
            raise ValueError("Message must be either a string or a list of dictionaries")

        # Override payload values with any provided keyword arguments
        for key, value in kwargs.items():
            if key in self.payload:
                self.payload[key] = value
        
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=self.payload
            )
            response.raise_for_status()
            response = response.json()
        except requests.RequestException:
            return None
        return response["choices"][0]["message"]["content"]
        