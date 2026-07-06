import json

import httpx
import pytest

from medtriage_mcp.api_client import MedTriageApiClient


@pytest.mark.asyncio
async def test_health_check_calls_agent_health_endpoint():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"status": "ok", "service": "agent"})

    client = MedTriageApiClient(
        base_url="http://agent.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.health_check()

    assert requests[0].method == "GET"
    assert str(requests[0].url) == "http://agent.local/health"
    assert result == {"ok": True, "data": {"status": "ok", "service": "agent"}}


@pytest.mark.asyncio
async def test_triage_patient_posts_expected_payload():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "urgence": "orange",
                "orientation": "medecin generaliste",
                "delai": "sous 24h",
                "conseils": ["Boire de l'eau"],
                "questions_complementaires": [],
                "justification": "Fievre persistante.",
                "message": "Consultez rapidement.",
                "disclaimer_medical": "Ceci ne remplace pas un avis medical.",
                "signals": [],
            },
        )

    client = MedTriageApiClient(
        base_url="http://agent.local/",
        transport=httpx.MockTransport(handler),
    )

    result = await client.triage_patient(
        symptomes="Fievre 39 depuis 2 jours",
        age=24,
        sexe="F",
        antecedents=["asthme"],
        medicaments=["paracetamol"],
        allergies=["penicilline"],
        photo_base64="abc123",
    )

    assert str(requests[0].url) == "http://agent.local/triage"
    assert json.loads(requests[0].content) == {
        "symptomes": "Fievre 39 depuis 2 jours",
        "age": 24,
        "sexe": "F",
        "antecedents": ["asthme"],
        "medicaments": ["paracetamol"],
        "allergies": ["penicilline"],
        "photo_base64": "abc123",
    }
    assert result["ok"] is True
    assert result["data"]["urgence"] == "orange"


@pytest.mark.asyncio
async def test_chat_triage_posts_message_context():
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "conversation_id": "conv-123",
                "urgence": "yellow",
                "orientation": "pharmacie",
                "delai": "aujourd'hui",
                "conseils": ["Surveillez l'evolution"],
                "questions_complementaires": ["Depuis quand ?"],
                "justification": "Symptomes moderes.",
                "message": "Pouvez-vous preciser la duree ?",
                "disclaimer_medical": "Ceci ne remplace pas un avis medical.",
                "signals": [],
            },
        )

    client = MedTriageApiClient(
        base_url="http://agent.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.chat_triage(
        message="J'ai mal a la gorge",
        conversation_id="conv-123",
        history=[{"role": "assistant", "content": "Bonjour"}],
        photo_base64=None,
    )

    assert str(requests[0].url) == "http://agent.local/chat"
    assert json.loads(requests[0].content) == {
        "message": "J'ai mal a la gorge",
        "conversation_id": "conv-123",
        "history": [{"role": "assistant", "content": "Bonjour"}],
    }
    assert result["ok"] is True
    assert result["data"]["conversation_id"] == "conv-123"


@pytest.mark.asyncio
async def test_client_returns_structured_error_when_agent_api_fails():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "service unavailable"})

    client = MedTriageApiClient(
        base_url="http://agent.local",
        transport=httpx.MockTransport(handler),
    )

    result = await client.health_check()

    assert result == {
        "ok": False,
        "error": {
            "type": "http_error",
            "status_code": 503,
            "message": "Agent API returned HTTP 503.",
            "details": {"detail": "service unavailable"},
        },
    }
