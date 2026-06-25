# MedTriageAI Agent

Scope: conversational agent, triage logic, and orchestration only.

This service does not implement the frontend, Azure Computer Vision, or the Azure ML model. It calls those modules through stable HTTP contracts when their URLs are configured.

## Run locally

```bash
cd agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Open:

```text
http://localhost:8000/docs
```

## Local ports

| Service | Port | URL |
|---|---:|---|
| Frontend | 3000 | `http://localhost:3000` |
| Agent IA | 8000 | `http://localhost:8000` |
| Computer Vision | 8001 | `http://localhost:8001` |
| ML Model | 8002 | `http://localhost:8002` |

## Main endpoint

```http
POST /triage
```

Example body:

```json
{
  "symptomes": "J'ai 39°C de fièvre, mal à la gorge et des frissons depuis 2 jours",
  "age": 24
}
```

## Chat with context

```http
POST /chat
```

The backend stores the recent conversation context by `conversation_id`. The frontend should reuse the `conversation_id` returned by the first response for the next messages.

First message:

```json
{
  "message": "J'ai de la fièvre"
}
```

Follow-up message:

```json
{
  "conversation_id": "<returned conversation_id>",
  "message": "depuis 2 jours"
}
```

## Microsoft Agent Framework boundary

`medtriage_agent.ms_agent` isolates the future Microsoft Agent Framework integration. The medical triage workflow itself stays in `orchestrator.py`, so it can be tested without a specific framework runtime.
