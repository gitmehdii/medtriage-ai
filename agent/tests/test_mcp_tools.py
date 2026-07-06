import pytest

from medtriage_mcp.tools import MedTriageTools


class RecordingClient:
    def __init__(self):
        self.calls = []

    async def health_check(self):
        self.calls.append(("health_check", {}))
        return {"ok": True, "data": {"status": "ok"}}

    async def triage_patient(self, **kwargs):
        self.calls.append(("triage_patient", kwargs))
        return {"ok": True, "data": {"urgence": "green"}}

    async def chat_triage(self, **kwargs):
        self.calls.append(("chat_triage", kwargs))
        return {"ok": True, "data": {"conversation_id": "conv-1"}}


@pytest.mark.asyncio
async def test_tools_delegate_health_check_to_api_client():
    client = RecordingClient()
    tools = MedTriageTools(client)

    result = await tools.health_check()

    assert result == {"ok": True, "data": {"status": "ok"}}
    assert client.calls == [("health_check", {})]


@pytest.mark.asyncio
async def test_tools_delegate_triage_patient_arguments_to_api_client():
    client = RecordingClient()
    tools = MedTriageTools(client)

    result = await tools.triage_patient(
        symptomes="Douleur thoracique",
        age=48,
        sexe="M",
        antecedents=["hypertension"],
        medicaments=["amlodipine"],
        allergies=[],
        photo_base64=None,
    )

    assert result == {"ok": True, "data": {"urgence": "green"}}
    assert client.calls == [
        (
            "triage_patient",
            {
                "symptomes": "Douleur thoracique",
                "age": 48,
                "sexe": "M",
                "antecedents": ["hypertension"],
                "medicaments": ["amlodipine"],
                "allergies": [],
                "photo_base64": None,
            },
        )
    ]


@pytest.mark.asyncio
async def test_tools_delegate_chat_triage_arguments_to_api_client():
    client = RecordingClient()
    tools = MedTriageTools(client)

    result = await tools.chat_triage(
        message="J'ai de la fievre",
        conversation_id="conv-1",
        history=[{"role": "assistant", "content": "Bonjour"}],
        photo_base64="image",
    )

    assert result == {"ok": True, "data": {"conversation_id": "conv-1"}}
    assert client.calls == [
        (
            "chat_triage",
            {
                "message": "J'ai de la fievre",
                "conversation_id": "conv-1",
                "history": [{"role": "assistant", "content": "Bonjour"}],
                "photo_base64": "image",
            },
        )
    ]
