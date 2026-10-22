from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from pydantic import BaseModel, SecretStr, field_validator

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    # One Microsoft Foundry (Azure AI Services) resource hosts both deployments and shares one key.
    azure_openai_api_key: SecretStr = SecretStr("")
    azure_openai_endpoint: str = ""
    azure_decision_deployment: str = "Decision-1"
    azure_gpt_deployment: str = "gpt-5-mini"
    jev_base_url: str = "https://api.typesafe.ai"
    jev_model: str = "jev-latest"

    @field_validator("azure_openai_endpoint", "jev_base_url")
    @classmethod
    def https_endpoint(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Configure an HTTPS endpoint without credentials or query parameters.")
        return value.rstrip("/")

    @field_validator("azure_openai_api_key")
    @classmethod
    def clean_key(cls, value: SecretStr) -> SecretStr:
        return SecretStr(value.get_secret_value().strip())

    @field_validator("azure_decision_deployment", "azure_gpt_deployment", "jev_model")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value or "/" in value or not value.isprintable():
            raise ValueError("Deployment and model names must be non-empty and contain no '/'.")
        return value

    @property
    def azure_origin(self) -> str:
        # Users often paste .../openai/v1 or a project URL; both models live at the resource root.
        parsed = urlsplit(self.azure_openai_endpoint)
        return f"https://{parsed.netloc}" if parsed.netloc else ""

    @property
    def decision_base_url(self) -> str:
        return f"{self.azure_origin}/providers/microsoft" if self.azure_origin else ""

    @property
    def gpt_base_url(self) -> str:
        return f"{self.azure_origin}/openai/v1" if self.azure_origin else ""

    @property
    def azure_ready(self) -> bool:
        return bool(self.azure_openai_api_key.get_secret_value() and self.azure_origin)

    @classmethod
    def load(cls) -> Settings:
        values = {**dotenv_values(ROOT / ".env"), **os.environ}
        data = {name: values[name.upper()] for name in cls.model_fields if values.get(name.upper())}
        return cls.model_validate(data)
