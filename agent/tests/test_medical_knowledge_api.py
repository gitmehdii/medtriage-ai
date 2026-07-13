import pytest
from fastapi.testclient import TestClient

from medical_knowledge_mcp.api import create_app
from test_medical_knowledge_tools import RecordingService


@pytest.fixture
def service() -> RecordingService:
    return RecordingService()


@pytest.fixture
def client(service: RecordingService) -> TestClient:
    return TestClient(create_app(service))


def test_health_reports_medical_knowledge_service_name_and_version(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "data": {
            "status": "ok",
            "service": "medical-knowledge-mcp",
            "version": "1.0.0",
        },
    }


def test_search_endpoint_returns_tool_envelope_and_delegates(client, service):
    response = client.post(
        "/knowledge/search",
        json={"query": "chest pain", "speciality": "cardiology", "country": "fr", "limit": 1},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["data"]["results"][0]["citation"]["retrieved_at"] == "2024-01-04T00:00:00Z"
    assert service.calls == [
        (
            "search",
            __import__("medical_knowledge_mcp.models", fromlist=["SearchRequest"]).SearchRequest(
                query="chest pain", speciality="cardiology", country="FR", limit=1
            ),
        )
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "pain", "country": "FRA"},
        {"query": "pain", "limit": 0},
        {"query": "pain", "unexpected": True},
    ],
)
def test_search_endpoint_returns_structured_validation_error(client, service, payload):
    response = client.post("/knowledge/search", json=payload)

    assert response.status_code == 422
    assert response.json()["ok"] is False
    assert response.json()["error"]["code"] == "validation_error"
    assert service.calls == []


def test_red_flags_endpoint_returns_tool_envelope_and_delegates(client, service):
    response = client.post("/knowledge/red-flags", json={"symptom": " chest pain ", "country": "fr"})

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["data"]["red_flags"][0]["severity"] == "critical"
    assert service.calls == [("red_flags", ("chest pain", "FR"))]


@pytest.mark.parametrize(
    "payload",
    [
        {"symptom": ""},
        {"symptom": "pain", "country": "FRA"},
        {"symptom": "pain", "unexpected": True},
    ],
)
def test_red_flags_endpoint_returns_structured_validation_error(client, service, payload):
    response = client.post("/knowledge/red-flags", json=payload)

    assert response.status_code == 422
    assert response.json()["ok"] is False
    assert response.json()["error"]["code"] == "validation_error"
    assert service.calls == []


def test_source_endpoint_returns_source_envelope_and_delegates(client, service):
    response = client.get("/knowledge/sources/has-chest-pain")

    assert response.status_code == 200
    assert response.json()["data"]["source"]["source_id"] == "has-chest-pain"
    assert service.calls == [("source", "has-chest-pain")]


def test_source_endpoint_returns_not_found_envelope(client):
    response = client.get("/knowledge/sources/missing")

    assert response.status_code == 404
    assert response.json()["ok"] is False
    assert response.json()["error"]["code"] == "not_found"


def test_source_endpoint_rejects_blank_source_id(client, service):
    response = client.get("/knowledge/sources/%20")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert service.calls == []
