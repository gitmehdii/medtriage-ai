from datetime import datetime, timezone

from medical_knowledge_mcp.models import KnowledgeError, SearchRequest, SourceRecord
from medical_knowledge_mcp.repository import KnowledgeRepository
from medical_knowledge_mcp.retrieval import SearchResponse


class MedicalKnowledgeService:
    def __init__(self, repository=None, retriever=None):
        self.repository = repository or KnowledgeRepository()
        self.retriever = retriever

    def search_medical_guidelines(self, request: SearchRequest) -> SearchResponse:
        if self.retriever is None:
            from medical_knowledge_mcp.retrieval import HybridRetriever
            self.retriever = HybridRetriever(self.repository)
        return self.retriever.search(request)

    def get_red_flags(self, symptom: str, country: str):
        return self.repository.get_red_flags(symptom, country)

    def get_source_details(self, source_id: str) -> SourceRecord | None:
        return self.repository.get_source(source_id)
