from typing import Any
from urllib.parse import quote

import httpx


class MedicalKnowledgeApiClient:
    """HTTP facade used by MedTriage MCP for the medical-knowledge service."""

    def __init__(self, base_url: str, timeout_seconds: float = 15, transport: httpx.AsyncBaseTransport | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def search_medical_guidelines(self, query: str, speciality: str | None = None, country: str = "FR", limit: int = 5):
        return await self._request("POST", "/knowledge/search", json=_compact_payload({"query": query, "speciality": speciality, "country": country, "limit": limit}))

    async def get_red_flags(self, symptom: str, country: str = "FR"):
        return await self._request("POST", "/knowledge/red-flags", json={"symptom": symptom, "country": country})

    async def get_source_details(self, source_id: str):
        return await self._request("GET", f"/knowledge/sources/{quote(source_id.strip(), safe='')}")

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None):
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.request(method, f"{self.base_url}{path}", json=json)
        except httpx.HTTPError as exc:
            return {"ok": False, "error": {"type": "network_error", "message": str(exc)}}
        if response.is_error:
            return {"ok": False, "error": {"type": "http_error", "status_code": response.status_code, "message": f"Medical knowledge API returned HTTP {response.status_code}.", "details": _safe_json(response)}}
        payload = _safe_json(response)
        if isinstance(payload, dict) and set(payload) >= {"ok", "data"}:
            return payload
        return {"ok": True, "data": payload}


def _compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}
