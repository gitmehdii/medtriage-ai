# Medical Knowledge MCP service

This container exposes the validated medical-knowledge HTTP API on port 8003. It searches its local corpus first and only uses configured, reviewed official-source fallback adapters. The production corpus intentionally starts empty: do not add source content until it has completed the review process below.

## Run

From the repository root:

```bash
docker compose up --build medical-knowledge
```

Health is available at `http://localhost:8003/health`. The service command inside the image is `python main.py`.

For local Python development, install the service requirements, expose the agent package on `PYTHONPATH`, and run the same command:

```bash
cd agent
pip install -r ../medical-knowledge-mcp/requirements.txt
$env:PYTHONPATH='.'
python ../medical-knowledge-mcp/main.py
```

## Configuration

All values are non-secret environment settings:

| Variable | Default | Purpose |
|---|---|---|
| `MEDICAL_KNOWLEDGE_PORT` | `8003` | HTTP port. |
| `MEDICAL_KNOWLEDGE_CORPUS_PATH` | `medical_knowledge_mcp/data/sources.json` | Local JSON corpus path. |
| `MEDICAL_KNOWLEDGE_FRESHNESS_DAYS` | `365` | Maximum age of verification before a local source is excluded. |
| `MEDICAL_KNOWLEDGE_ALLOWED_DOMAINS` | HAS, Ministry of Health, ameli, WHO domains | Reviewed official source allow-list. |
| `MEDICAL_KNOWLEDGE_FALLBACK_BASE_URLS` | empty | Optional official-source fallback endpoints; empty disables fallback. |
| `MEDICAL_KNOWLEDGE_FALLBACK_TIMEOUT_SECONDS` | `5` | Per-fallback timeout. |

`MEDICAL_KNOWLEDGE_SERVICE_URL=http://medical-knowledge:8003` is set on the agent by Docker Compose. No credentials are required or stored in this service.

## Corpus import and update

The corpus is `agent/medical_knowledge_mcp/data/sources.json`. Keep it as an object with `sources` and `red_flags` arrays. Each source must contain an HTTPS allow-listed URL, source ID, organization, country, speciality, publication date, update date, verification timestamp, content hash, active status, excerpt, and terms. A red-flag entry must reference an imported source ID.

To import an approved corpus revision, replace only that file, run the knowledge test suite, validate Compose, then rebuild and restart the service:

```bash
cd agent
$env:PYTHONPATH='.'; pytest tests/test_medical_knowledge_retrieval.py tests/test_medical_knowledge_api.py -q
cd ..
docker compose config
docker compose up -d --build medical-knowledge
```

Do not import patient narratives, credentials, scraped pages, or unapproved source data.

## Source governance

Before import or a fallback-domain change, a reviewer must confirm that the organization is official, the exact host is trusted, the content is current for the intended country and speciality, and all citation dates and content hash are correct. Keep a review record outside the service corpus. Re-check sources before the freshness window expires and deactivate a source immediately if it is withdrawn or superseded.

## Verification, rollback, and outages

Verify a release with `/health` and fixture-backed searches; every returned result must retain its source URL, publication/update date, verification date, and retrieval timestamp. If a corpus revision is wrong, restore the last reviewed `sources.json`, rerun the import checks above, and rebuild `medical-knowledge`. Do not edit data in a running container.

If this service is unavailable, the agent continues triage without knowledge evidence and reports the evidence status as unavailable. It must not invent citations or block a triage response. An empty local corpus and disabled fallback return no evidence rather than attempting unreviewed network access.
