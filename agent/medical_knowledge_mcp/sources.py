from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import urlparse

import httpx
from pydantic import ValidationError

from medical_knowledge_mcp.config import get_settings
from medical_knowledge_mcp.fallback import OfficialSourceUnavailable
from medical_knowledge_mcp.models import Citation, GuidelineResult, SearchRequest


def _is_allow_listed(url: str, allowed_domains: Iterable[str]) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    return parsed.scheme == "https" and any(
        hostname == domain.lower().rstrip(".") or hostname.endswith(f".{domain.lower().rstrip('.')}")
        for domain in allowed_domains
    )


_CONTROLLED_TERMS = {
    "chest", "pain", "thoracic", "douleur", "thoracique", "fever", "fièvre",
    "cough", "toux", "breathing", "difficulty", "respiratory", "headache",
    "vomiting", "diarrhea", "rash", "bleeding", "pregnancy", "trauma",
}


def _safe_external_query(query: str) -> str:
    """Keep patient narratives out of URLs sent to official fallback providers."""
    terms = [term for term in query.casefold().replace("-", " ").split() if term in _CONTROLLED_TERMS]
    return " ".join(dict.fromkeys(terms)) or "general symptom triage"


class OfficialSourceAdapter:
    def __init__(self, base_url: str, *, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        if not _is_allow_listed(base_url, settings.allowed_domains):
            raise ValueError("official source base URL is not allow-listed")
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=settings.fallback_timeout_seconds)

    def search(self, request: SearchRequest) -> list[GuidelineResult]:
        params: dict[str, Any] = {"query": _safe_external_query(request.query), "country": request.country, "limit": request.limit}
        if request.speciality:
            params["speciality"] = request.speciality
        response = self._client.get(f"{self._base_url}/search", params=params)
        response.raise_for_status()
        payload = response.json()
        documents = payload.get("results", []) if isinstance(payload, dict) else payload
        if not isinstance(documents, list):
            raise OfficialSourceUnavailable("official source returned an invalid response")

        retrieved_at = datetime.now(timezone.utc)
        results: list[GuidelineResult] = []
        for document in documents:
            result = self._to_result(document, retrieved_at)
            if result is not None:
                results.append(result)
        return results[: request.limit]

    @staticmethod
    def _to_result(document: object, retrieved_at: datetime) -> GuidelineResult | None:
        if not isinstance(document, dict):
            return None
        values = dict(document)
        values["retrieved_at"] = retrieved_at
        citation_values = {
            key: values[key]
            for key in ("source_id", "url", "title", "publication_date", "last_update_date", "last_verified_at")
            if key in values
        }
        citation_values["retrieved_at"] = retrieved_at
        values["citation"] = citation_values
        try:
            return GuidelineResult(**values)
        except ValidationError:
            return None


class OfficialSourceRegistry:
    def __init__(self, adapters: Iterable[OfficialSourceAdapter] | None = None) -> None:
        if adapters is None:
            adapters = [OfficialSourceAdapter(url) for url in get_settings().fallback_base_urls]
        self._adapters = list(adapters)

    def search(self, request: SearchRequest) -> list[GuidelineResult]:
        if not self._adapters:
            raise OfficialSourceUnavailable()
        results: list[GuidelineResult] = []
        succeeded = False
        for adapter in self._adapters:
            try:
                results.extend(adapter.search(request))
                succeeded = True
            except (httpx.HTTPError, OfficialSourceUnavailable, ValueError):
                continue
        if not succeeded:
            raise OfficialSourceUnavailable()
        return results[: request.limit]
