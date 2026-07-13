import json
from datetime import date, datetime, timezone

from medical_knowledge_mcp.models import SearchRequest
from medical_knowledge_mcp.repository import KnowledgeRepository
from medical_knowledge_mcp.retrieval import KnowledgeRetriever


FRESH_DATE = "2026-07-01T00:00:00+00:00"
STALE_DATE = "2024-01-01T00:00:00+00:00"


def _source(source_id: str, **overrides):
    value = {
        "source_id": source_id,
        "title": "Chest pain assessment",
        "organization": "Haute Autorite de Sante",
        "country": "FR",
        "speciality": "emergency medicine",
        "url": f"https://www.has-sante.fr/guidelines/{source_id}",
        "publication_date": "2025-01-01",
        "last_update_date": "2026-06-01",
        "last_verified_at": FRESH_DATE,
        "content_hash": f"sha256:{source_id}",
        "active": True,
        "excerpt": "Assess chest pain promptly and escalate warning signs.",
        "terms": ["chest pain", "douleur thoracique"],
    }
    value.update(overrides)
    return value


def _write_corpus(tmp_path):
    corpus = {
        "sources": [
            _source("chest-primary"),
            _source(
                "chest-secondary",
                title="Chest pain referral pathway",
                excerpt="Chest pain referral pathway for emergency assessment.",
                terms=["chest", "pain", "thoracique", "referral"],
            ),
            _source("cardiology-fr", speciality="cardiology"),
            _source("chest-us", country="US"),
            _source("inactive-chest", active=False),
            _source(
                "stale-chest",
                publication_date="2023-01-01",
                last_update_date="2023-06-01",
                last_verified_at=STALE_DATE,
            ),
            _source(
                "breathing-red-flags",
                title="Breathing difficulty escalation",
                excerpt="Urgent assessment for severe breathing difficulty.",
                terms=["breathing difficulty", "dyspnea"],
            ),
        ],
        "red_flags": [
            {
                "symptom": "Breathing difficulty",
                "country": "FR",
                "severity": "critical",
                "action": "Call emergency services immediately.",
                "evidence_excerpt": "Severe breathing difficulty requires urgent assessment.",
                "source_id": "breathing-red-flags",
            },
            {
                "symptom": "breathing difficulty",
                "country": "FR",
                "severity": "high",
                "action": "Do not use this stale guidance.",
                "evidence_excerpt": "Stale guidance must not be returned.",
                "source_id": "stale-chest",
            },
        ],
    }
    corpus_path = tmp_path / "sources.json"
    corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
    return corpus_path


def _repository(tmp_path):
    return KnowledgeRepository(
        _write_corpus(tmp_path),
        freshness_days=365,
        today=date(2026, 7, 13),
    )


def test_search_applies_country_speciality_active_and_freshness_filters(tmp_path):
    results = _repository(tmp_path).search(
        SearchRequest(query="chest pain", country="FR", speciality="emergency medicine")
    )

    assert [result.source_id for result in results] == ["chest-primary", "chest-secondary"]


def test_search_ranks_normalized_terms_deterministically(tmp_path):
    repository = _repository(tmp_path)
    request = SearchRequest(query="Douleur thoracique", country="FR")

    first = repository.search(request)
    second = repository.search(request)

    assert [result.source_id for result in first] == ["cardiology-fr", "chest-primary", "chest-secondary"]
    assert [result.source_id for result in second] == [result.source_id for result in first]
    assert first[0].relevance_score > first[-1].relevance_score


def test_source_lookup_returns_known_source_and_none_for_unknown_id(tmp_path):
    repository = _repository(tmp_path)

    assert repository.get_source("chest-primary").title == "Chest pain assessment"
    assert repository.get_source("unknown-source") is None


def test_red_flag_lookup_normalizes_symptom_and_excludes_stale_sources(tmp_path):
    red_flags = _repository(tmp_path).get_red_flags("BREATHING   difficulty", "fr")

    assert len(red_flags) == 1
    assert red_flags[0].severity == "critical"
    assert red_flags[0].citation.source_id == "breathing-red-flags"


def test_retriever_returns_local_response_and_empty_result_status(tmp_path):
    retriever = KnowledgeRetriever(_repository(tmp_path))

    response = retriever.search(SearchRequest(query="chest pain", country="FR", limit=1))
    empty_response = retriever.search(SearchRequest(query="rash", country="FR"))

    assert response.fallback_used is False
    assert [result.source_id for result in response.results] == ["cardiology-fr"]
    assert empty_response.results == []
    assert empty_response.fallback_used is False
    assert empty_response.retrieved_at.tzinfo == timezone.utc
