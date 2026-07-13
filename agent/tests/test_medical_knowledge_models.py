from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from medical_knowledge_mcp import models
from medical_knowledge_mcp.config import MedicalKnowledgeSettings
from medical_knowledge_mcp.models import (
    Citation,
    ErrorResponse,
    GuidelineResult,
    KnowledgeError,
    RedFlag,
    SearchRequest,
    SourceRecord,
)


def source_kwargs(**overrides):
    values = {
        "source_id": "has-chest-pain",
        "title": "Douleur thoracique",
        "organization": "Haute Autorité de Santé",
        "country": "FR",
        "speciality": "emergency medicine",
        "url": "https://www.has-sante.fr/jcms/c_1234567/fr/douleur-thoracique",
        "publication_date": date(2024, 1, 1),
        "last_update_date": date(2024, 6, 1),
        "last_verified_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "content_hash": "sha256:abc123",
        "active": True,
    }
    values.update(overrides)
    return values


def citation_kwargs(**overrides):
    values = {
        "source_id": "has-chest-pain",
        "url": "https://www.has-sante.fr/jcms/c_1234567/fr/douleur-thoracique",
        "title": "Douleur thoracique",
        "publication_date": date(2024, 1, 1),
        "last_update_date": date(2024, 6, 1),
        "last_verified_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "retrieved_at": datetime(2025, 1, 2, tzinfo=timezone.utc),
    }
    values.update(overrides)
    return values


def test_accepts_valid_french_has_source():
    source = SourceRecord(**source_kwargs())

    assert source.country == "FR"
    assert str(source.url).startswith("https://www.has-sante.fr/")
    assert source.model_dump(mode="json")["publication_date"] == "2024-01-01"


def test_rejects_missing_source_url():
    with pytest.raises(ValidationError):
        SourceRecord(**source_kwargs(url=None))


def test_rejects_unsupported_source_domain():
    with pytest.raises(ValidationError, match="allow-listed"):
        SourceRecord(**source_kwargs(url="https://example.com/guideline"))


def test_rejects_invalid_dates():
    with pytest.raises(ValidationError):
        SourceRecord(**source_kwargs(last_update_date=date(2023, 12, 31)))


def test_rejects_invalid_country_code():
    with pytest.raises(ValidationError):
        SourceRecord(**source_kwargs(country="FRA"))


def test_search_request_defaults_to_five_results_and_validates_country():
    request = SearchRequest(query="chest pain")

    assert request.limit == 5
    assert request.country == "FR"
    with pytest.raises(ValidationError):
        SearchRequest(query="fever", country="ZZ")


def test_guideline_result_red_flag_and_citation_are_structured():
    source = SourceRecord(**source_kwargs())
    citation = Citation(**citation_kwargs())
    result = GuidelineResult(
        source_id=source.source_id,
        title=source.title,
        organization=source.organization,
        country=source.country,
        url=source.url,
        publication_date=source.publication_date,
        last_update_date=source.last_update_date,
        last_verified_at=source.last_verified_at,
        excerpt="Urgent assessment is required.",
        relevance_score=0.9,
        citation=citation,
    )
    red_flag = RedFlag(
        symptom="chest pain",
        country="FR",
        severity="high",
        action="Call emergency services.",
        evidence_excerpt=result.excerpt,
        citation=citation,
    )

    assert result.citation.source_id == source.source_id
    assert red_flag.country == "FR"


@pytest.mark.parametrize(
    "field",
    ["url", "publication_date", "last_update_date", "last_verified_at", "retrieved_at"],
)
def test_citation_requires_complete_provenance_metadata(field):
    values = citation_kwargs()
    values.pop(field)

    with pytest.raises(ValidationError):
        Citation(**values)


def test_guideline_result_rejects_invalid_source_chronology():
    source = SourceRecord(**source_kwargs())

    with pytest.raises(ValidationError, match="guideline dates are not chronological"):
        GuidelineResult(
            source_id=source.source_id,
            title=source.title,
            organization=source.organization,
            country=source.country,
            url=source.url,
            publication_date=date(2024, 6, 2),
            last_update_date=source.last_update_date,
            last_verified_at=source.last_verified_at,
            excerpt="Urgent assessment is required.",
            relevance_score=0.9,
            citation=Citation(**citation_kwargs()),
        )


def test_url_validation_honors_configured_allowed_domains(monkeypatch):
    monkeypatch.setattr(
        models,
        "get_settings",
        lambda: MedicalKnowledgeSettings(allowed_domains=["example.org"]),
    )

    source = SourceRecord(**source_kwargs(url="https://sub.example.org/guideline"))

    assert source.url.host == "sub.example.org"
    with pytest.raises(ValidationError, match="allow-listed"):
        SourceRecord(**source_kwargs())


def test_error_response_ok_is_always_false():
    response = ErrorResponse(error=KnowledgeError(code="invalid_request", message="Invalid request"))

    assert response.ok is False
    with pytest.raises(ValidationError):
        ErrorResponse(ok=True, error=response.error)


def test_settings_include_service_defaults():
    settings = MedicalKnowledgeSettings()

    assert settings.port == 8003
    assert settings.corpus_path
    assert settings.freshness_days > 0
    assert settings.fallback_timeout_seconds > 0
    assert settings.agent_url
    assert "has-sante.fr" in settings.allowed_domains
