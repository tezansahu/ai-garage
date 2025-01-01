import os
import requests
from dotenv import load_dotenv

class LLMClient:
    """
    A class to interact with GPT  models via API (either OpenAI or Azure OpenAI, based on the availability of API keys).
    Attributes:
        headers (dict): HTTP headers for the API request.
        endpoint (str): The API endpoint URL.
        api_key (str): The API key for authentication.
        deployment_name (str): The deployment name for Azure OpenAI (if applicable).
        api_version (str): The API version for Azure OpenAI (if applicable).
        payload (dict): The payload for the API request.
    Methods:
        __init__():
            Initializes the LLM class, sets up API keys, endpoints, and headers.
        send_message(message, **kwargs):
            Sends a message to the API and returns the response.
            Args:
                message (str or list): The message to send. Can be a string or a list of dictionaries.
                **kwargs: Additional keyword arguments to override payload values.
            Returns:
                str: The content of the response message.
            Raises:
                ValueError: If the message is not a string or a list of dictionaries.
    """
    
    def __init__(self):
        load_dotenv()
        self.headers = {}
        self.endpoint = ""

        if "AZURE_OPENAI_API_KEY" in os.environ and not (os.environ['AZURE_OPENAI_API_KEY'] == "" or os.environ['AZURE_OPENAI_API_KEY'] is None):
            self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
            self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            self.deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
            self.api_version = os.getenv('AZURE_OPENAI_API_VERSION')

            self.headers = {
                'Content-Type': 'application/json',
                "api-key": self.api_key,
            }

            self.endpoint = f'{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions?api-version={self.api_version}'
        elif "OPENAI_API_KEY" in os.environ and not (os.environ['OPENAI_API_KEY'] == "" or os.environ['OPENAI_API_KEY'] is None):
            self.api_key = os.getenv('OPENAI_API_KEY')
            self.endpoint = "https://api.openai.com/v1/chat/completions"
            self.headers = {
                'Content-Type': 'application/json',
                "Authorization": f"Bearer {self.api_key}",
            }
        else:
            raise ValueError("API key not found in environment variables")

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
        