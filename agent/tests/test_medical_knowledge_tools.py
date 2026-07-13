import asyncio
from datetime import date, datetime, timezone

import pytest

from medical_knowledge_mcp.models import (
    Citation,
    GuidelineResult,
    KnowledgeError,
    RedFlag,
    SearchRequest,
    SourceRecord,
)
from medical_knowledge_mcp.retrieval import SearchResponse
from medical_knowledge_mcp.service import MedicalKnowledgeService
from medical_knowledge_mcp.tools import MedicalKnowledgeTools


RETRIEVED_AT = datetime(2024, 1, 4, tzinfo=timezone.utc)


class RecordingService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.search_response = SearchResponse(
            results=[_guideline()],
            fallback_used=False,
            retrieved_at=RETRIEVED_AT,
        )

    def search_medical_guidelines(self, request: SearchRequest) -> SearchResponse:
        self.calls.append(("search", request))
        return self.search_response

    def get_red_flags(self, symptom: str, country: str) -> list[RedFlag]:
        self.calls.append(("red_flags", (symptom, country)))
        return [_red_flag()]

    def get_source_details(self, source_id: str) -> SourceRecord | None:
        self.calls.append(("source", source_id))
        return _source() if source_id == "has-chest-pain" else None


class RecordingRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def get_red_flags(self, symptom: str, country: str) -> list[RedFlag]:
        self.calls.append(("red_flags", (symptom, country)))
        return [_red_flag()]

    def get_source(self, source_id: str) -> SourceRecord | None:
        self.calls.append(("source", source_id))
        return _source()


class RecordingRetriever:
    def __init__(self) -> None:
        self.calls: list[SearchRequest] = []

    def search(self, request: SearchRequest) -> SearchResponse:
        self.calls.append(request)
        return SearchResponse(results=[_guideline()], retrieved_at=RETRIEVED_AT)


def test_service_delegates_to_repository_and_retriever():
    repository = RecordingRepository()
    retriever = RecordingRetriever()
    service = MedicalKnowledgeService(repository=repository, retriever=retriever)
    request = SearchRequest(query="chest pain")

    assert service.search_medical_guidelines(request).results[0].source_id == "has-chest-pain"
    assert service.get_red_flags("chest pain", "FR")[0].severity == "critical"
    assert service.get_source_details("has-chest-pain").source_id == "has-chest-pain"
    assert retriever.calls == [request]
    assert repository.calls == [
        ("red_flags", ("chest pain", "FR")),
        ("source", "has-chest-pain"),
    ]


def test_search_tool_validates_normalizes_and_delegates_to_service():
    service = RecordingService()
    tools = MedicalKnowledgeTools(service)

    result = tools.search_medical_guidelines(
        " chest pain ",
        speciality="cardiology",
        country="fr",
        limit=2,
    )

    assert result["ok"] is True
    assert result["data"]["results"][0]["source_id"] == "has-chest-pain"
    assert result["data"]["fallback_used"] is False
    assert result["data"]["retrieved_at"] == "2024-01-04T00:00:00Z"
    assert service.calls == [
        (
            "search",
            SearchRequest(query="chest pain", speciality="cardiology", country="FR", limit=2),
        )
    ]


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"query": " "}, "query"),
        ({"query": "pain", "country": "FRA"}, "country"),
        ({"query": "pain", "limit": 0}, "limit"),
        ({"query": "pain", "speciality": " "}, "speciality"),
    ],
)
def test_search_tool_rejects_invalid_inputs_without_delegating(kwargs, field):
    service = RecordingService()

    result = MedicalKnowledgeTools(service).search_medical_guidelines(**kwargs)

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"
    assert any(error["loc"][-1] == field for error in result["error"]["details"]["errors"])
    assert service.calls == []


def test_search_tool_preserves_structured_retrieval_error():
    service = RecordingService()
    service.search_response = SearchResponse(
        fallback_used=True,
        error=KnowledgeError(
            code="knowledge_unavailable",
            message="Official medical knowledge sources are currently unavailable.",
            details={"fallback_used": True},
        ),
        retrieved_at=RETRIEVED_AT,
    )

    result = MedicalKnowledgeTools(service).search_medical_guidelines("rare symptom")

    assert result == {
        "ok": False,
        "error": {
            "code": "knowledge_unavailable",
            "message": "Official medical knowledge sources are currently unavailable.",
            "details": {"fallback_used": True},
        },
    }


def test_red_flags_tool_validates_and_delegates_to_service():
    service = RecordingService()

    result = MedicalKnowledgeTools(service).get_red_flags(" chest pain ", country="fr")

    assert result["ok"] is True
    assert result["data"]["red_flags"][0]["citation"]["retrieved_at"] == "2024-01-04T00:00:00Z"
    assert service.calls == [("red_flags", ("chest pain", "FR"))]


def test_red_flags_tool_returns_validation_error_without_delegating():
    service = RecordingService()

    result = MedicalKnowledgeTools(service).get_red_flags(" ", country="FRA")

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"
    assert service.calls == []


def test_red_flags_tool_rejects_non_string_symptom_without_raising():
    service = RecordingService()

    result = MedicalKnowledgeTools(service).get_red_flags(None)  # type: ignore[arg-type]

    assert result["ok"] is False
    assert result["error"]["code"] == "validation_error"
    assert service.calls == []


def test_source_details_tool_trims_id_and_delegates():
    service = RecordingService()

    result = MedicalKnowledgeTools(service).get_source_details(" has-chest-pain ")

    assert result["ok"] is True
    assert result["data"]["source"]["url"] == "https://www.has-sante.fr/chest-pain"
    assert service.calls == [("source", "has-chest-pain")]


def test_source_details_tool_returns_not_found_error():
    service = RecordingService()

    result = MedicalKnowledgeTools(service).get_source_details("unknown")

    assert result == {
        "ok": False,
        "error": {
            "code": "not_found",
            "message": "Medical knowledge source was not found.",
            "details": {"source_id": "unknown"},
        },
    }


def test_mcp_server_registers_exactly_three_tools_with_citation_date_requirements():
    from medical_knowledge_mcp.server import mcp

    registered = asyncio.run(mcp.list_tools())

    assert {tool.name for tool in registered} == {
        "search_medical_guidelines",
        "get_red_flags",
        "get_source_details",
    }
    for tool in registered:
        description = tool.description.lower()
        assert "citation" in description
        assert "publication" in description
        assert "update" in description
        assert "verification" in description
        assert "retrieval" in description


def _source() -> SourceRecord:
    return SourceRecord(
        source_id="has-chest-pain",
        title="Chest pain guidance",
        organization="HAS",
        country="FR",
        speciality="cardiology",
        url="https://www.has-sante.fr/chest-pain",
        publication_date=date(2024, 1, 1),
        last_update_date=date(2024, 1, 2),
        last_verified_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
        content_hash="abc",
    )


def _citation() -> Citation:
    source = _source()
    return Citation(
        source_id=source.source_id,
        title=source.title,
        url=source.url,
        publication_date=source.publication_date,
        last_update_date=source.last_update_date,
        last_verified_at=source.last_verified_at,
        retrieved_at=RETRIEVED_AT,
    )


def _guideline() -> GuidelineResult:
    source = _source()
    return GuidelineResult(
        source_id=source.source_id,
        title=source.title,
        organization=source.organization,
        country=source.country,
        url=source.url,
        publication_date=source.publication_date,
        last_update_date=source.last_update_date,
        last_verified_at=source.last_verified_at,
        excerpt="Urgent assessment is required for concerning chest pain.",
        relevance_score=1,
        citation=_citation(),
        retrieved_at=RETRIEVED_AT,
    )


def _red_flag() -> RedFlag:
    return RedFlag(
        symptom="chest pain",
        country="FR",
        severity="critical",
        action="Call emergency services.",
        evidence_excerpt="Sudden chest pain with breathing difficulty requires urgent care.",
        citation=_citation(),
    )
