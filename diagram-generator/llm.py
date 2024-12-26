import os
import requests
from dotenv import load_dotenv

class AzureOpenAI:
    """
    A class to interact with the Azure OpenAI service.
    Methods
    -------
    __init__():
        Initializes the AzureOpenAI instance with environment variables and sets up the endpoint and headers.
    send_message(message, **kwargs):
        Sends a message to the Azure OpenAI service and returns the response.
    Attributes
    ----------
    api_key : str
        The API key for the Azure OpenAI service, loaded from environment variables.
    endpoint : str
        The endpoint URL for the Azure OpenAI service, constructed from environment variables.
    deployment_name : str
        The deployment name for the Azure OpenAI service, loaded from environment variables.
    api_version : str
        The API version for the Azure OpenAI service, loaded from environment variables.
    headers : dict
        The headers to be used in the HTTP request to the Azure OpenAI service.
    payload : dict
        The payload to be sent in the HTTP request to the Azure OpenAI service.
    Raises
    ------
    ValueError
        If the message parameter in send_message is neither a string nor a list of dictionaries.
    requests.RequestException
        If there is an issue with the HTTP request to the Azure OpenAI service.
    """
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
        