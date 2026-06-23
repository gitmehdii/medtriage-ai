from medtriage_agent.orchestrator import TriageOrchestrator
from medtriage_agent.schemas import TriageRequest, TriageResponse


class MedTriageAgent:
    """Framework-neutral agent facade.

    Keep the medical workflow here small and delegate decisions to the tested
    orchestrator. A Microsoft Agent Framework runtime can wrap this facade
    without changing the triage logic.
    """

    def __init__(self, orchestrator: TriageOrchestrator):
        self.orchestrator = orchestrator

    async def handle_triage(self, request: TriageRequest) -> TriageResponse:
        return await self.orchestrator.triage(request)


def build_ms_agent_runtime(agent: MedTriageAgent) -> MedTriageAgent:
    """Return the current agent facade.

    This is the integration boundary for Microsoft Agent Framework. The exact
    SDK package is intentionally isolated here because the rest of the service
    should not depend on framework-specific decorators or runtime objects.
    """

    return agent
