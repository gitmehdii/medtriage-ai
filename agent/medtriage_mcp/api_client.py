from typing import Any

import httpx


class MedTriageApiClient:
    """HTTP facade used by MCP tools to call the MedTriage agent API."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 15,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def health_check(self) -> dict[str, Any]:
        return await self._request("GET", "/health")

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
        payload = _compact_payload(
            {
                "symptomes": symptomes,
                "age": age,
                "sexe": sexe,
                "antecedents": antecedents or [],
                "medicaments": medicaments or [],
                "allergies": allergies or [],
                "photo_base64": photo_base64,
            }
        )
        return await self._request("POST", "/triage", json=payload)

    async def chat_triage(
        self,
        message: str,
        conversation_id: str | None = None,
        history: list[dict[str, str]] | None = None,
        photo_base64: str | None = None,
    ) -> dict[str, Any]:
        payload = _compact_payload(
            {
                "message": message,
                "conversation_id": conversation_id,
                "history": history or [],
                "photo_base64": photo_base64,
            }
        )
        return await self._request("POST", "/chat", json=payload)

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.request(method, url, json=json)
        except httpx.HTTPError as exc:
            return {
                "ok": False,
                "error": {
                    "type": "network_error",
                    "message": str(exc),
                },
            }

        if response.is_error:
            return {
                "ok": False,
                "error": {
                    "type": "http_error",
                    "status_code": response.status_code,
                    "message": f"Agent API returned HTTP {response.status_code}.",
                    "details": _safe_json(response),
                },
            }

        return {"ok": True, "data": _safe_json(response)}


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}
