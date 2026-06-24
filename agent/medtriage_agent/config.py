from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MedTriageAI Agent"
    app_env: str = "local"
    agent_port: int = 8000

    llm_provider: str = Field(default="none", pattern="^(ollama|gemini|none)$")
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    vision_service_url: str = ""
    ml_service_url: str = ""
    request_timeout_seconds: float = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
