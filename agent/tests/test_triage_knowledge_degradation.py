import asyncio

import pytest

from medtriage_agent.llm import DeterministicProvider
from medtriage_agent.orchestrator import TriageOrchestrator
from medtriage_agent.schemas import ModuleSignal, TriageRequest


class StubModules:
    async def classify_symptoms(self, request):
        return ModuleSignal(source="ml-model", available=False)

    async def analyze_photo(self, request):
        return ModuleSignal(source="vision", available=False)


class SlowKnowledgeClient:
    async def get_red_flags(self, symptom, country="FR"):
        await asyncio.sleep(0.05)
        return {"ok": True, "data": {"ok": True, "data": {"red_flags": []}}}

    async def search_medical_guidelines(
        self, query, speciality=None, country="FR", limit=5
    ):
        await asyncio.sleep(0.05)
        return {"ok": True, "data": {"ok": True, "data": {"results": []}}}


class ErrorKnowledgeClient:
    async def get_red_flags(self, symptom, country="FR"):
        return {
            "ok": False,
            "error": {"type": "network_error", "message": "service unavailable"},
        }

    async def search_medical_guidelines(
        self, query, speciality=None, country="FR", limit=5
    ):
        raise RuntimeError("connection reset")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("knowledge_client", "timeout"),
    [(SlowKnowledgeClient(), 0.001), (ErrorKnowledgeClient(), 0.1)],
)
async def test_knowledge_failure_degrades_without_breaking_triage(
    knowledge_client, timeout
):
    orchestrator = TriageOrchestrator(
        StubModules(),
        DeterministicProvider(),
        knowledge_client=knowledge_client,
        knowledge_timeout_seconds=timeout,
    )

    response = await orchestrator.triage(
        TriageRequest(symptomes="douleur thoracique")
    )

    assert response.message
    assert response.citations == []
    assert response.metadata == {"knowledge_status": "unavailable"}


@pytest.mark.asyncio
async def test_no_knowledge_client_preserves_deterministic_triage_behavior():
    orchestrator = TriageOrchestrator(StubModules(), DeterministicProvider())

    response = await orchestrator.triage(TriageRequest(symptomes="fatigue légère"))

    assert response.message.startswith("Niveau vert.")
    assert response.citations == []
    assert response.metadata == {"knowledge_status": "not_configured"}
