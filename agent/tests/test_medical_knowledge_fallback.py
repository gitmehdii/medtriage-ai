from datetime import datetime, timezone

import httpx
import pytest

from medical_knowledge_mcp.fallback import OfficialSourceUnavailable
from medical_knowledge_mcp.models import SearchRequest
from medical_knowledge_mcp.retrieval import HybridRetriever
from medical_knowledge_mcp.sources import OfficialSourceAdapter, OfficialSourceRegistry


def _official_result(**overrides):
    result = {
        "source_id": "has-chest-pain",
        "title": "Chest pain guidance",
        "organization": "Haute Autorite de Sante",
        "country": "FR",
        "url": "https://www.has-sante.fr/guidelines/chest-pain",
        "publication_date": "2025-01-01",
        "last_update_date": "2026-06-01",
        "last_verified_at": "2026-06-02T00:00:00+00:00",
        "excerpt": "Assess chest pain promptly.",
        "relevance_score": 0.8,
    }
    result.update(overrides)
    return result


class _Repository:
    def __init__(self, results):
        self.results = results

    def search(self, request):
        return self.results[: request.limit]


def _adapter(handler):
    return OfficialSourceAdapter(
        "https://www.has-sante.fr",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_adapter_returns_allow_list_validated_official_results_with_retrieval_time():
    def handler(request):
        assert request.url.path == "/search"
        assert request.url.params["query"] == "chest pain"
        return httpx.Response(200, json={"results": [_official_result()]})

    results = _adapter(handler).search(SearchRequest(query="chest pain"))

    assert [result.source_id for result in results] == ["has-chest-pain"]
    assert results[0].retrieved_at.tzinfo == timezone.utc
    assert results[0].citation.retrieved_at == results[0].retrieved_at


def test_adapter_discards_results_with_urls_outside_the_allow_list():
    results = _adapter(
        lambda request: httpx.Response(200, json={"results": [_official_result(url="https://example.com/advice")]})
    ).search(SearchRequest(query="chest pain"))

    assert results == []


@pytest.mark.parametrize("status_code", [500, 503])
def test_registry_raises_structured_unavailable_error_for_non_successful_responses(status_code):
    registry = OfficialSourceRegistry([_adapter(lambda request: httpx.Response(status_code))])

    with pytest.raises(OfficialSourceUnavailable, match="official sources unavailable"):
        registry.search(SearchRequest(query="chest pain"))


def test_hybrid_retriever_uses_official_fallback_when_local_results_are_empty():
    registry = OfficialSourceRegistry([_adapter(lambda request: httpx.Response(200, json=[_official_result()]))])

    response = HybridRetriever(_Repository([]), registry, reliability_threshold=0.7).search(
        SearchRequest(query="chest pain")
    )

    assert response.fallback_used is True
    assert [result.source_id for result in response.results] == ["has-chest-pain"]
    assert response.error is None


def test_hybrid_retriever_uses_fallback_when_local_reliability_is_below_threshold():
    local_result = _adapter(lambda request: httpx.Response(200, json=[_official_result(source_id="local", relevance_score=0.4)])).search(
        SearchRequest(query="chest pain")
    )[0]
    registry = OfficialSourceRegistry([_adapter(lambda request: httpx.Response(200, json=[_official_result()]))])

    response = HybridRetriever(_Repository([local_result]), registry, reliability_threshold=0.7).search(
        SearchRequest(query="chest pain")
    )

    assert response.fallback_used is True
    assert [result.source_id for result in response.results] == ["has-chest-pain", "local"]


def test_hybrid_retriever_prioritizes_fallback_before_applying_limit():
    local_result = _adapter(lambda request: httpx.Response(200, json=[_official_result(source_id="local", relevance_score=0.4)])).search(
        SearchRequest(query="chest pain")
    )[0]
    registry = OfficialSourceRegistry([_adapter(lambda request: httpx.Response(200, json=[_official_result()]))])

    response = HybridRetriever(_Repository([local_result]), registry, reliability_threshold=0.7).search(
        SearchRequest(query="chest pain", limit=1)
    )

    assert response.fallback_used is True
    assert [result.source_id for result in response.results] == ["has-chest-pain"]


def test_hybrid_retriever_returns_local_results_when_fallback_times_out():
    def timeout(request):
        raise httpx.ReadTimeout("slow official source", request=request)

    local_result = _adapter(lambda request: httpx.Response(200, json=[_official_result(source_id="local")])).search(
        SearchRequest(query="chest pain")
    )[0]
    response = HybridRetriever(
        _Repository([local_result]), OfficialSourceRegistry([_adapter(timeout)]), reliability_threshold=0.9
    ).search(SearchRequest(query="chest pain"))

    assert [result.source_id for result in response.results] == ["local"]
    assert response.fallback_used is True
    assert response.error is None


def test_hybrid_retriever_returns_structured_unavailable_response_without_local_results():
    registry = OfficialSourceRegistry([_adapter(lambda request: httpx.Response(503))])

    response = HybridRetriever(_Repository([]), registry).search(SearchRequest(query="chest pain"))

    assert response.results == []
    assert response.error.code == "knowledge_unavailable"
    assert response.error.details["fallback_used"] is True
