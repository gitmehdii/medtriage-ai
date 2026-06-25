import pytest

from medtriage_agent.llm import DeterministicProvider
from medtriage_agent.orchestrator import TriageOrchestrator
from medtriage_agent.schemas import ModuleSignal, TriageRequest, UrgencyLevel


class StubModules:
    async def classify_symptoms(self, request):
        return ModuleSignal(source="ml-model", available=False)

    async def analyze_photo(self, request):
        return ModuleSignal(source="vision", available=False)


class OrangeMLModules:
    async def classify_symptoms(self, request):
        return ModuleSignal(source="ml-model", urgency=UrgencyLevel.orange, confidence=0.8)

    async def analyze_photo(self, request):
        return ModuleSignal(source="vision", available=False)


@pytest.mark.asyncio
async def test_orchestrator_keeps_rule_red_priority():
    orchestrator = TriageOrchestrator(StubModules(), DeterministicProvider())

    response = await orchestrator.triage(TriageRequest(symptomes="perte de connaissance"))

    assert response.urgence == UrgencyLevel.red
    assert response.orientation == "urgence vitale ou potentiellement vitale"


@pytest.mark.asyncio
async def test_orchestrator_promotes_external_module_urgency():
    orchestrator = TriageOrchestrator(OrangeMLModules(), DeterministicProvider())

    response = await orchestrator.triage(TriageRequest(symptomes="fatigue légère depuis hier"))

    assert response.urgence == UrgencyLevel.orange


@pytest.mark.asyncio
async def test_orchestrator_returns_conversation_id():
    orchestrator = TriageOrchestrator(StubModules(), DeterministicProvider())

    response = await orchestrator.triage(
        TriageRequest(symptomes="J'ai de la fièvre", conversation_id="conversation-1")
    )

    assert response.conversation_id == "conversation-1"
