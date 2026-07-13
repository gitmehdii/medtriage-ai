from datetime import datetime, timezone

from pydantic import BaseModel, Field

from medical_knowledge_mcp.config import get_settings
from medical_knowledge_mcp.fallback import OfficialSourceUnavailable
from medical_knowledge_mcp.models import GuidelineResult, KnowledgeError, SearchRequest
from medical_knowledge_mcp.repository import KnowledgeRepository
from medical_knowledge_mcp.sources import OfficialSourceRegistry


class SearchResponse(BaseModel):
    results: list[GuidelineResult] = Field(default_factory=list)
    fallback_used: bool = False
    error: KnowledgeError | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeRetriever:
    def __init__(self, repository: KnowledgeRepository | None = None) -> None:
        self._repository = repository or KnowledgeRepository()

    def search(self, request: SearchRequest) -> SearchResponse:
        return SearchResponse(results=self._repository.search(request))


class HybridRetriever:
    def __init__(
        self,
        repository: KnowledgeRepository | None = None,
        registry: OfficialSourceRegistry | None = None,
        *,
        reliability_threshold: float | None = None,
    ) -> None:
        settings = get_settings()
        self._repository = repository or KnowledgeRepository()
        self._registry = registry or OfficialSourceRegistry()
        self._reliability_threshold = (
            settings.fallback_reliability_threshold if reliability_threshold is None else reliability_threshold
        )

    def search(self, request: SearchRequest) -> SearchResponse:
        local_results = self._repository.search(request)
        reliable_results = [
            result for result in local_results if result.relevance_score >= self._reliability_threshold
        ]
        fallback_required = len(reliable_results) < request.limit
        if not fallback_required:
            return SearchResponse(results=local_results)
        try:
            fallback_results = self._registry.search(request)
        except OfficialSourceUnavailable:
            if local_results:
                return SearchResponse(results=local_results, fallback_used=True)
            return SearchResponse(
                fallback_used=True,
                error=KnowledgeError(
                    code="knowledge_unavailable",
                    message="Official medical knowledge sources are currently unavailable.",
                    details={"fallback_used": True},
                ),
            )
        fallback_source_ids = {result.source_id for result in fallback_results}
        combined_results = fallback_results + [
            result for result in local_results if result.source_id not in fallback_source_ids
        ]
        return SearchResponse(results=combined_results[: request.limit], fallback_used=True)
