from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from medical_knowledge_mcp.service import MedicalKnowledgeService
from medical_knowledge_mcp.tools import MedicalKnowledgeTools, _error


class SearchBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str
    speciality: str | None = None
    country: str = "FR"
    limit: int = 5


class RedFlagsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symptom: str
    country: str = "FR"


def create_app(service=None) -> FastAPI:
    service = service or MedicalKnowledgeService()
    tools = MedicalKnowledgeTools(service)
    app = FastAPI(title="Medical Knowledge MCP", version="1.0.0")

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            error = dict(error)
            error.pop("ctx", None)
            errors.append(error)
        return JSONResponse(status_code=422, content=_error("validation_error", "Invalid medical knowledge request.", {"errors": errors}))

    @app.get("/health")
    async def health():
        return {"ok": True, "data": {"status": "ok", "service": "medical-knowledge-mcp", "version": "1.0.0"}}

    @app.post("/knowledge/search")
    async def search(body: SearchBody):
        result = tools.search_medical_guidelines(**body.model_dump())
        return JSONResponse(status_code=422 if not result["ok"] and result["error"]["code"] == "validation_error" else 200, content=result)

    @app.post("/knowledge/red-flags")
    async def red_flags(body: RedFlagsBody):
        result = tools.get_red_flags(**body.model_dump())
        return JSONResponse(status_code=422 if not result["ok"] and result["error"]["code"] == "validation_error" else 200, content=result)

    @app.get("/knowledge/sources/{source_id}")
    async def source_details(source_id: str):
        result = tools.get_source_details(source_id)
        code = result.get("error", {}).get("code") if not result["ok"] else None
        status = 404 if code == "not_found" else 422 if code == "validation_error" else 200
        return JSONResponse(status_code=status, content=result)

    return app


app = create_app()
