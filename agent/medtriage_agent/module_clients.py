from typing import Any

import httpx

from medtriage_agent.config import Settings
from medtriage_agent.schemas import ModuleSignal, TriageRequest, UrgencyLevel


class ExternalModuleClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def classify_symptoms(self, request: TriageRequest) -> ModuleSignal:
        if not self.settings.ml_service_url:
            return ModuleSignal(source="ml-model", available=False, summary="ML service URL not configured.")

        payload = {
            "symptomes": request.symptomes,
            "age": request.age,
            "sexe": request.sexe,
            "antecedents": request.antecedents,
            "medicaments": request.medicaments,
            "allergies": request.allergies,
        }
        return await self._post_signal(self.settings.ml_service_url, "/predict", "ml-model", payload)

    async def analyze_photo(self, request: TriageRequest) -> ModuleSignal:
        if not request.photo_base64:
            return ModuleSignal(source="vision", available=False, summary="No photo provided.")
        if not self.settings.vision_service_url:
            return ModuleSignal(source="vision", available=False, summary="Vision service URL not configured.")

        payload = {"image_base64": request.photo_base64}
        return await self._post_signal(self.settings.vision_service_url, "/analyze", "vision", payload)

    async def _post_signal(
        self, base_url: str, path: str, source: str, payload: dict[str, Any]
    ) -> ModuleSignal:
        url = base_url.rstrip("/") + path
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            return ModuleSignal(source=source, available=False, summary=f"{source} unavailable: {exc}")

        return ModuleSignal(
            source=source,
            available=True,
            urgency=_parse_urgency(data.get("urgence") or data.get("urgency")),
            confidence=data.get("confidence"),
            summary=data.get("summary") or data.get("justification"),
            raw=data,
        )


def _parse_urgency(value: Any) -> UrgencyLevel | None:
    if value is None:
        return None
    normalized = str(value).lower()
    mapping = {
        "green": UrgencyLevel.green,
        "vert": UrgencyLevel.green,
        "yellow": UrgencyLevel.yellow,
        "jaune": UrgencyLevel.yellow,
        "orange": UrgencyLevel.orange,
        "red": UrgencyLevel.red,
        "rouge": UrgencyLevel.red,
    }
    return mapping.get(normalized)
