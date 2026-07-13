from medical_knowledge_mcp.config import MedicalKnowledgeSettings
from medtriage_agent.config import Settings


def test_medical_knowledge_uses_safe_local_defaults(monkeypatch):
    monkeypatch.delenv("MEDICAL_KNOWLEDGE_PORT", raising=False)
    monkeypatch.delenv("MEDICAL_KNOWLEDGE_FRESHNESS_DAYS", raising=False)
    monkeypatch.delenv("MEDICAL_KNOWLEDGE_FALLBACK_BASE_URLS", raising=False)

    settings = MedicalKnowledgeSettings(_env_file=None)

    assert settings.port == 8003
    assert settings.freshness_days == 365
    assert settings.fallback_timeout_seconds == 5.0
    assert settings.fallback_base_urls == []


def test_medical_knowledge_configuration_honors_environment_overrides(monkeypatch):
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_FRESHNESS_DAYS", "30")
    monkeypatch.setenv("MEDICAL_KNOWLEDGE_SERVICE_URL", "http://medical-knowledge:8003")

    knowledge_settings = MedicalKnowledgeSettings(_env_file=None)
    agent_settings = Settings(_env_file=None)

    assert knowledge_settings.freshness_days == 30
    assert agent_settings.medical_knowledge_service_url == "http://medical-knowledge:8003"
