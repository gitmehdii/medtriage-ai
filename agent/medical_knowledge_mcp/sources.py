from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import re
from typing import Any, Iterable
from urllib.parse import quote_plus, urljoin, urlparse

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


_DATE_PATTERNS = (
    re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b"),
)


class _SearchPageParser(HTMLParser):
    """Small dependency-free parser for official search result pages."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            title = " ".join(" ".join(self._text).split())
            if title:
                self.links.append((self._href, title))
            self._href = None
            self._text = []


class OfficialWebSearchAdapter:
    """Search an official website's own search page and cite the source page."""

    def __init__(self, name: str, search_url: str, domain: str, organization: str, country: str, *, client: httpx.Client | None = None) -> None:
        settings = get_settings()
        if not _is_allow_listed(search_url, settings.allowed_domains) or not _is_allow_listed(f"https://{domain}", settings.allowed_domains):
            raise ValueError("official web connector is not allow-listed")
        self.name = name
        self.search_url = search_url
        self.domain = domain
        self.organization = organization
        self.country = country
        self._client = client or httpx.Client(timeout=settings.fallback_timeout_seconds, follow_redirects=True)

    def search(self, request: SearchRequest) -> list[GuidelineResult]:
        query = _safe_external_query(request.query)
        response = self._client.get(self.search_url, params={"q": query, "query": query, "text": query})
        response.raise_for_status()
        parser = _SearchPageParser()
        parser.feed(response.text)
        results: list[GuidelineResult] = []
        seen: set[str] = set()
        for href, title in parser.links:
            url = urljoin(str(response.url), href)
            if url in seen or not _is_allow_listed(url, [self.domain]):
                continue
            seen.add(url)
            result = self._result_from_page(url, title, request)
            if result is not None:
                results.append(result)
            if len(results) >= request.limit:
                break
        return results

    def _result_from_page(self, url: str, fallback_title: str, request: SearchRequest) -> GuidelineResult | None:
        page = self._client.get(url)
        page.raise_for_status()
        text = page.text
        dates = _extract_dates(text)
        if not dates:
            return None
        updated = max(dates)
        published = min(dates)
        retrieved = datetime.now(timezone.utc)
        title = _extract_meta(text, "og:title") or _extract_title(text) or fallback_title
        excerpt = _extract_meta(text, "description") or "Source officielle consultée; vérifier le contenu intégral."
        source_id = f"{self.name}:{sha256(url.encode()).hexdigest()[:16]}"
        values = {
            "source_id": source_id,
            "title": title[:500],
            "organization": self.organization,
            "country": request.country if request.country == self.country else self.country,
            "url": url,
            "publication_date": published,
            "last_update_date": updated,
            "last_verified_at": retrieved,
            "excerpt": excerpt[:2000],
            "relevance_score": 0.8,
            "retrieved_at": retrieved,
        }
        values["citation"] = {key: values[key] for key in ("source_id", "url", "title", "publication_date", "last_update_date", "last_verified_at")}
        values["citation"]["retrieved_at"] = retrieved
        try:
            return GuidelineResult(**values)
        except ValidationError:
            return None


def _extract_dates(text: str) -> list[Any]:
    from datetime import date
    dates: list[date] = []
    for pattern in _DATE_PATTERNS:
        for match in pattern.finditer(text):
            parts = [int(part) for part in match.groups()]
            y, m, d = parts if len(parts) == 3 and parts[0] > 1900 else (parts[2], parts[1], parts[0])
            try:
                candidate = date(y, m, d)
            except ValueError:
                continue
            if candidate <= datetime.now(timezone.utc).date():
                dates.append(candidate)
    return dates


def _extract_meta(html: str, name: str) -> str | None:
    match = re.search(rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)', html, re.I)
    return match.group(1).strip() if match else None


def _extract_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split()) if match else None


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
            settings = get_settings()
            configured = {name.strip().lower() for name in settings.fallback_sources.split(",") if name.strip()}
            web_adapters = [
                OfficialWebSearchAdapter("has", "https://www.has-sante.fr/jcms/fc_2875171/fr/resultat-de-recherche", "has-sante.fr", "Haute Autorité de Santé", "FR"),
                OfficialWebSearchAdapter("who", "https://www.who.int/search", "who.int", "Organisation mondiale de la Santé", "CH"),
                OfficialWebSearchAdapter("nhs", "https://www.nhs.uk/search/results", "nhs.uk", "National Health Service", "GB"),
            ]
            adapters = [adapter for adapter in web_adapters if adapter.name in configured]
            adapters.extend(OfficialSourceAdapter(url) for url in settings.fallback_base_urls)
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
