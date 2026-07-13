import json
import importlib
import sys

import httpx
import pytest

from medtriage_mcp.knowledge_client import MedicalKnowledgeApiClient


def _load_server(monkeypatch: pytest.MonkeyPatch, knowledge_url: str | None):
    if knowledge_url is None:
        monkeypatch.delenv("MEDICAL_KNOWLEDGE_SERVICE_URL", raising=False)
    else:
        monkeypatch.setenv("MEDICAL_KNOWLEDGE_SERVICE_URL", knowledge_url)
    import medtriage_mcp.config as config

    config.get_mcp_settings.cache_clear()
    sys.modules.pop("medtriage_mcp.server", None)
    return importlib.import_module("medtriage_mcp.server")


def test_knowledge_tools_are_registered_only_when_service_url_is_configured(monkeypatch):
    disabled_server = _load_server(monkeypatch, None)

    assert set(disabled_server.mcp._tool_manager._tools) == {"health_check", "triage_patient", "chat_triage"}

    enabled_server = _load_server(monkeypatch, "http://knowledge.local")

    assert set(enabled_server.mcp._tool_manager._tools) == {
        "health_check",
        "triage_patient",
        "chat_triage",
        "search_medical_guidelines",
        "get_red_flags",
        "get_source_details",
    }


@pytest.mark.asyncio
async def test_search_medical_guidelines_posts_compact_search_payload():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "data": {"results": []}})

    client = MedicalKnowledgeApiClient(
        base_url="http://knowledge.local/",
        transport=httpx.MockTransport(handler),
    )

    result = await client.search_medical_guidelines("chest pain", speciality=None, country="FR", limit=3)

    assert requests[0].method == "POST"
    assert str(requests[0].url) == "http://knowledge.local/knowledge/search"
    assert json.loads(requests[0].content) == {"query": "chest pain", "country": "FR", "limit": 3}
    assert result == {"ok": True, "data": {"results": []}}


@pytest.mark.asyncio
async def test_get_red_flags_posts_expected_payload():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "data": {"red_flags": []}})

    client = MedicalKnowledgeApiClient(
        base_url="http://knowledge.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.get_red_flags("breathing difficulty", country="BE")

    assert str(requests[0].url) == "http://knowledge.local/knowledge/red-flags"
    assert json.loads(requests[0].content) == {"symptom": "breathing difficulty", "country": "BE"}
    assert result["ok"] is True


@pytest.mark.asyncio
async def test_get_source_details_uses_source_endpoint():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "data": {"source": {"source_id": "has-chest-pain"}}})

    client = MedicalKnowledgeApiClient(
        base_url="http://knowledge.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.get_source_details("has-chest-pain")

    assert requests[0].method == "GET"
    assert str(requests[0].url) == "http://knowledge.local/knowledge/sources/has-chest-pain"
    assert result["data"]["source"]["source_id"] == "has-chest-pain"


@pytest.mark.asyncio
async def test_get_source_details_encodes_source_id_as_single_path_segment():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"ok": True, "data": {"source": None}})

    client = MedicalKnowledgeApiClient("http://knowledge.local", transport=httpx.MockTransport(handler))
    await client.get_source_details("../health")

    assert str(requests[0].url) == "http://knowledge.local/knowledge/sources/..%2Fhealth"


@pytest.mark.asyncio
async def test_client_returns_structured_network_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("knowledge unavailable", request=request)

    client = MedicalKnowledgeApiClient(
        base_url="http://knowledge.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.get_red_flags("chest pain")

    assert result == {
        "ok": False,
        "error": {"type": "network_error", "message": "knowledge unavailable"},
    }


@pytest.mark.asyncio
async def test_client_returns_structured_http_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "service unavailable"})

    client = MedicalKnowledgeApiClient(
        base_url="http://knowledge.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.search_medical_guidelines("fever")

    assert result == {
        "ok": False,
        "error": {
            "type": "http_error",
            "status_code": 503,
            "message": "Medical knowledge API returned HTTP 503.",
            "details": {"detail": "service unavailable"},
        },
    }
