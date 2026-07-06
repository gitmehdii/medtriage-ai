from typing import Any, Protocol


class MedTriageClient(Protocol):
    async def health_check(self) -> dict[str, Any]:
        raise NotImplementedError

    async def triage_patient(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError

    async def chat_triage(self, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError


class MedTriageTools:
    def __init__(self, client: MedTriageClient):
        self.client = client

    async def health_check(self) -> dict[str, Any]:
        """Check whether the MedTriage agent API is reachable."""
        return await self.client.health_check()

    async def triage_patient(
        self,
        symptomes: str,
        age: int | None = None,
        sexe: str | None = None,
        antecedents: list[str] | None = None,
        medicaments: list[str] | None = None,
        allergies: list[str] | None = None,
        photo_base64: str | None = None,
    ) -> dict[str, Any]:
        """Run medical triage from symptom text and optional patient context."""
        return await self.client.triage_patient(
            symptomes=symptomes,
            age=age,
            sexe=sexe,
            antecedents=antecedents,
            medicaments=medicaments,
            allergies=allergies,
            photo_base64=photo_base64,
        )

    async def chat_triage(
        self,
        message: str,
        conversation_id: str | None = None,
        history: list[dict[str, str]] | None = None,
        photo_base64: str | None = None,
    ) -> dict[str, Any]:
        """Continue a MedTriage conversation and return structured triage guidance."""
        return await self.client.chat_triage(
            message=message,
            conversation_id=conversation_id,
            history=history,
            photo_base64=photo_base64,
        )
