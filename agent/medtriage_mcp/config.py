from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class McpSettings(BaseSettings):
    medtriage_agent_api_url: str = "http://localhost:8000"
    medtriage_mcp_timeout_seconds: float = 15
    medical_knowledge_service_url: str | None = None
    medical_knowledge_mcp_timeout_seconds: float = 15

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_mcp_settings() -> McpSettings:
    return McpSettings()
