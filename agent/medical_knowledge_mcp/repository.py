import json
import re
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from medical_knowledge_mcp.config import get_settings
from medical_knowledge_mcp.models import Citation, GuidelineResult, RedFlag, SearchRequest, SourceRecord


def _normalized_terms(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    return tuple(re.findall(r"[a-z0-9]+", normalized.casefold()))


class KnowledgeRepository:
    def __init__(
        self,
        corpus_path: str | Path | None = None,
        *,
        freshness_days: int | None = None,
        today: date | None = None,
    ) -> None:
        settings = get_settings()
        self._corpus_path = Path(corpus_path or settings.corpus_path)
        self._freshness_days = freshness_days or settings.freshness_days
        self._today = today or date.today()
        self._sources: dict[str, SourceRecord] = {}
        self._source_documents: dict[str, dict[str, Any]] = {}
        self._red_flag_documents: list[dict[str, Any]] = []
        self._load()

    def search(self, request: SearchRequest) -> list[GuidelineResult]:
        query_terms = set(_normalized_terms(request.query))
        candidates: list[tuple[float, str]] = []
        for source_id, source in self._sources.items():
            if not self._is_available(source) or source.country != request.country:
                continue
            if request.speciality and _normalized_terms(source.speciality) != _normalized_terms(request.speciality):
                continue
            matched_terms = query_terms.intersection(self._document_terms(self._source_documents[source_id], source))
            if matched_terms:
                candidates.append((len(matched_terms) / len(query_terms), source_id))

        candidates.sort(key=lambda candidate: (-candidate[0], candidate[1]))
        return [self._to_guideline_result(source_id, score) for score, source_id in candidates[: request.limit]]

    def get_source(self, source_id: str) -> SourceRecord | None:
        return self._sources.get(source_id)

    def get_red_flags(self, symptom: str, country: str) -> list[RedFlag]:
        symptom_terms = _normalized_terms(symptom)
        country = country.upper()
        red_flags: list[RedFlag] = []
        for document in self._red_flag_documents:
            source = self._sources.get(document["source_id"])
            if (
                source is None
                or source.country != country
                or not self._is_available(source)
                or _normalized_terms(document["symptom"]) != symptom_terms
            ):
                continue
            red_flags.append(
                RedFlag(
                    symptom=document["symptom"],
                    country=source.country,
                    severity=document["severity"],
                    action=document["action"],
                    evidence_excerpt=document["evidence_excerpt"],
                    citation=self._citation_for(source),
                )
            )
        return red_flags

    def _load(self) -> None:
        try:
            corpus = json.loads(self._corpus_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ValueError(f"Knowledge corpus was not found: {self._corpus_path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"Knowledge corpus is not valid JSON: {self._corpus_path}") from error
        if not isinstance(corpus, dict):
            raise ValueError("Knowledge corpus must be a JSON object")
        sources = corpus.get("sources", [])
        red_flags = corpus.get("red_flags", [])
        if not isinstance(sources, list) or not isinstance(red_flags, list):
            raise ValueError("Knowledge corpus sources and red_flags must be arrays")

        for document in sources:
            if not isinstance(document, dict):
                raise ValueError("Knowledge corpus sources must be objects")
            source = SourceRecord(**{key: value for key, value in document.items() if key not in {"excerpt", "terms"}})
            if source.source_id in self._sources:
                raise ValueError(f"Knowledge corpus contains duplicate source ID: {source.source_id}")
            self._sources[source.source_id] = source
            self._source_documents[source.source_id] = document

        for document in red_flags:
            if not isinstance(document, dict) or not isinstance(document.get("source_id"), str):
                raise ValueError("Knowledge corpus red flags must include a source_id")
            self._red_flag_documents.append(document)

    def _is_available(self, source: SourceRecord) -> bool:
        return source.active and (self._today - source.last_verified_at.date()).days <= self._freshness_days

    @staticmethod
    def _document_terms(document: dict[str, Any], source: SourceRecord) -> set[str]:
        fields = [source.title, source.organization, source.speciality, document.get("excerpt", "")]
        fields.extend(str(term) for term in document.get("terms", []))
        return set(_normalized_terms(" ".join(fields)))

    def _to_guideline_result(self, source_id: str, relevance_score: float) -> GuidelineResult:
        source = self._sources[source_id]
        document = self._source_documents[source_id]
        retrieved_at = datetime.now(timezone.utc)
        return GuidelineResult(
            source_id=source.source_id,
            title=source.title,
            organization=source.organization,
            country=source.country,
            url=source.url,
            publication_date=source.publication_date,
            last_update_date=source.last_update_date,
            last_verified_at=source.last_verified_at,
            excerpt=document["excerpt"],
            relevance_score=relevance_score,
            citation=self._citation_for(source, retrieved_at),
            retrieved_at=retrieved_at,
        )

    @staticmethod
    def _citation_for(source: SourceRecord, retrieved_at: datetime | None = None) -> Citation:
        return Citation(
            source_id=source.source_id,
            url=source.url,
            title=source.title,
            publication_date=source.publication_date,
            last_update_date=source.last_update_date,
            last_verified_at=source.last_verified_at,
            retrieved_at=retrieved_at or datetime.now(timezone.utc),
        )
