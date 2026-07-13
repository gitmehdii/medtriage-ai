from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from medical_knowledge_mcp.models import KnowledgeError, SearchRequest


def _error(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"ok": False, "error": KnowledgeError(code=code, message=message, details=details or {}).model_dump(mode="json")}


def _validation_details(exc: ValidationError) -> dict[str, Any]:
    errors = []
    for error in exc.errors():
        error = dict(error)
        error.pop("ctx", None)
        errors.append(error)
    return {"errors": errors}


def _data(value: Any) -> dict[str, Any]:
    def serialize(item: Any) -> Any:
        if hasattr(item, "model_dump"):
            return item.model_dump(mode="json")
        if isinstance(item, datetime):
            return item.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        if isinstance(item, list):
            return [serialize(entry) for entry in item]
        if isinstance(item, dict):
            return {key: serialize(entry) for key, entry in item.items()}
        return item

    value = serialize(value)
    return {"ok": True, "data": value}


class MedicalKnowledgeTools:
    def __init__(self, service):
        self.service = service

    def search_medical_guidelines(self, query: str, speciality: str | None = None, country: str = "FR", limit: int = 5):
        try:
            if speciality is not None and not speciality.strip():
                raise ValueError("speciality must not be blank")
            request = SearchRequest(query=query, speciality=speciality, country=country, limit=limit)
        except ValidationError as exc:
            return _error("validation_error", "Invalid medical knowledge search request.", _validation_details(exc))
        except ValueError:
            return _error("validation_error", "Invalid medical knowledge search request.", {"errors": [{"loc": ["speciality"], "msg": "speciality must not be blank", "type": "value_error"}]})
        try:
            response = self.service.search_medical_guidelines(request)
        except Exception as exc:
            return _error("upstream_error", "Medical knowledge search failed.", {"type": exc.__class__.__name__})
        if response.error:
            return _error(response.error.code, response.error.message, response.error.details)
        return _data(response)

    def get_red_flags(self, symptom: str, country: str = "FR"):
        try:
            if not isinstance(symptom, str) or not symptom.strip():
                raise ValueError("symptom must not be blank")
            request = SearchRequest(query=symptom, country=country)
        except (ValidationError, ValueError) as exc:
            details = _validation_details(exc) if isinstance(exc, ValidationError) else {}
            return _error("validation_error", "Invalid red-flag request.", details)
        try:
            flags = self.service.get_red_flags(request.query, request.country)
        except Exception as exc:
            return _error("upstream_error", "Red-flag lookup failed.", {"type": exc.__class__.__name__})
        return _data({"red_flags": flags, "status": "validated_entries_found" if flags else "no_validated_entry"})

    def get_source_details(self, source_id: str):
        source_id = source_id.strip() if isinstance(source_id, str) else ""
        if not source_id:
            return _error("validation_error", "source_id must not be blank.")
        source = self.service.get_source_details(source_id)
        if source is None:
            return _error("not_found", "Medical knowledge source was not found.", {"source_id": source_id})
        now = datetime.now(timezone.utc)
        age_days = (now.date() - source.last_verified_at.date()).days
        freshness = "inactive" if not source.active else "stale" if age_days > 365 else "fresh"
        return _data({"source": source, "freshness_status": freshness, "retrieved_at": now})
