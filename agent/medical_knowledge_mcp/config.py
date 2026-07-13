from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MedicalKnowledgeSettings(BaseSettings):
    port: int = Field(default=8003, ge=1, le=65535, validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_PORT", "port"))
    corpus_path: str = Field(default="medical_knowledge_mcp/data/sources.json", validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_CORPUS_PATH", "corpus_path"))
    freshness_days: int = Field(default=365, ge=1, validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_FRESHNESS_DAYS", "freshness_days"))
    allowed_domains: list[str] = Field(
        default_factory=lambda: ["has-sante.fr", "sante.gouv.fr", "ameli.fr", "who.int"],
        validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_ALLOWED_DOMAINS", "allowed_domains"),
    )
    fallback_timeout_seconds: float = Field(
        default=5.0,
        gt=0,
        validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_FALLBACK_TIMEOUT_SECONDS", "fallback_timeout_seconds"),
    )
    fallback_base_urls: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_FALLBACK_BASE_URLS", "fallback_base_urls"),
    )
    fallback_reliability_threshold: float = Field(
        default=0.7,
        ge=0,
        le=1,
        validation_alias=AliasChoices(
            "MEDICAL_KNOWLEDGE_FALLBACK_RELIABILITY_THRESHOLD", "fallback_reliability_threshold"
        ),
    )
    agent_url: str = Field(
        default="http://localhost:8000",
        validation_alias=AliasChoices("MEDICAL_KNOWLEDGE_AGENT_URL", "agent_url"),
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


Settings = MedicalKnowledgeSettings


@lru_cache
def get_settings() -> MedicalKnowledgeSettings:
    return MedicalKnowledgeSettings()
