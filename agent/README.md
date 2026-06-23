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
uvicorn medtriage_agent.api:app --reload
```

Open:

```text
http://localhost:8000/docs
```

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

## Microsoft Agent Framework boundary

`medtriage_agent.ms_agent` isolates the future Microsoft Agent Framework integration. The medical triage workflow itself stays in `orchestrator.py`, so it can be tested without a specific framework runtime.
