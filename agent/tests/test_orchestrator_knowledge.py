from datetime import datetime, timezone

import pytest

from medtriage_agent.config import Settings
from medtriage_agent.orchestrator import TriageOrchestrator
from medtriage_agent.schemas import ModuleSignal, TriageRequest


class StubModules:
    async def classify_symptoms(self, request):
        return ModuleSignal(source="ml-model", available=False)

    async def analyze_photo(self, request):
        return ModuleSignal(source="vision", available=False)


class RecordingProvider:
    def __init__(self):
        self.calls = []

    async def compose_response(self, **kwargs):
        self.calls.append(kwargs)
        return "Réponse LLM fondée sur les références fournies."


class SuccessfulKnowledgeClient:
    def __init__(self, citation):
        self.citation = citation
        self.calls = []

    async def get_red_flags(self, symptom, country="FR"):
        self.calls.append(("red_flags", symptom, country))
        return {
            "ok": True,
            "data": {
                "ok": True,
                "data": {
                    "red_flags": [
                        {
                            "symptom": "douleur thoracique",
                            "country": "FR",
                            "severity": "critical",
                            "action": "Appeler immédiatement le 15 ou le 112.",
                            "evidence_excerpt": "Une douleur thoracique brutale est un signe d'alerte.",
                            "citation": self.citation,
                        }
                    ]
                },
            },
        }

    async def search_medical_guidelines(
        self, query, speciality=None, country="FR", limit=5
    ):
        self.calls.append(("guidelines", query, speciality, country, limit))
        return {
            "ok": True,
            "data": {
                "ok": True,
                "data": {
                    "results": [
                        {
                            "source_id": "has-chest-pain",
                            "title": "Prise en charge de la douleur thoracique",
                            "organization": "HAS",
                            "country": "FR",
                            "url": "https://www.has-sante.fr/chest-pain",
                            "publication_date": "2024-01-01",
                            "last_update_date": "2024-02-01",
                            "last_verified_at": "2024-03-01T00:00:00Z",
                            "excerpt": "Évaluer sans délai les signes de gravité.",
                            "relevance_score": 0.98,
                            "citation": self.citation,
                            "retrieved_at": "2024-03-02T00:00:00Z",
                        }
                    ],
                    "fallback_used": False,
                    "retrieved_at": "2024-03-02T00:00:00Z",
                },
            },
        }


def citation_payload():
    return {
        "source_id": "has-chest-pain",
        "url": "https://www.has-sante.fr/chest-pain",
        "title": "Prise en charge de la douleur thoracique",
        "publication_date": "2024-01-01",
        "last_update_date": "2024-02-01",
        "last_verified_at": "2024-03-01T00:00:00Z",
        "retrieved_at": "2024-03-02T00:00:00Z",
    }


@pytest.mark.asyncio
async def test_orchestrator_passes_only_delimited_evidence_and_returns_citations():
    provider = RecordingProvider()
    knowledge = SuccessfulKnowledgeClient(citation_payload())
    orchestrator = TriageOrchestrator(
        StubModules(),
        provider,
        knowledge_client=knowledge,
        knowledge_timeout_seconds=0.1,
    )

    response = await orchestrator.triage(
        TriageRequest(symptomes="douleur thoracique brutale")
    )

    assert knowledge.calls == [
        ("red_flags", "douleur thoracique brutale", "FR"),
        ("guidelines", "douleur thoracique brutale", None, "FR", 5),
    ]
    llm_justification = provider.calls[0]["justification"]
    assert "BEGIN UNTRUSTED MEDICAL REFERENCE CONTEXT" in llm_justification
    assert "END UNTRUSTED MEDICAL REFERENCE CONTEXT" in llm_justification
    assert "Évaluer sans délai les signes de gravité." in llm_justification
    assert "Appeler immédiatement le 15 ou le 112." in llm_justification
    assert '"knowledge_status": "available"' in llm_justification
    assert response.justification not in {"", llm_justification}
    assert response.metadata == {"knowledge_status": "available"}
    assert len(response.citations) == 1
    assert response.citations[0].source_id == "has-chest-pain"
    assert response.citations[0].retrieved_at == datetime(
        2024, 3, 2, tzinfo=timezone.utc
    )


def test_agent_api_builds_optional_knowledge_client_from_settings():
    from medtriage_agent.api import _build_knowledge_client

    disabled = Settings(medical_knowledge_service_url=None)
    assert _build_knowledge_client(disabled) is None

    enabled = Settings(
        medical_knowledge_service_url="http://knowledge.local/",
        medical_knowledge_timeout_seconds=2.5,
    )
    client = _build_knowledge_client(enabled)

    assert client.base_url == "http://knowledge.local"
    assert client.timeout_seconds == 2.5

