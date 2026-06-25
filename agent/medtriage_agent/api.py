from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medtriage_agent.config import get_settings
from medtriage_agent.llm import build_llm_provider
from medtriage_agent.module_clients import ExternalModuleClient
from medtriage_agent.ms_agent import MedTriageAgent, build_ms_agent_runtime
from medtriage_agent.orchestrator import TriageOrchestrator
from medtriage_agent.schemas import ChatRequest, TriageRequest, TriageResponse


settings = get_settings()
modules = ExternalModuleClient(settings)
llm = build_llm_provider(settings)
orchestrator = TriageOrchestrator(modules=modules, llm=llm)
agent = build_ms_agent_runtime(MedTriageAgent(orchestrator))

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent", "environment": settings.app_env}


@app.post("/triage", response_model=TriageResponse)
async def triage(request: TriageRequest) -> TriageResponse:
    return await agent.handle_triage(request)


@app.post("/chat", response_model=TriageResponse)
async def chat(request: ChatRequest) -> TriageResponse:
    triage_request = TriageRequest(
        symptomes=request.message,
        photo_base64=request.photo_base64,
        conversation_id=request.conversation_id,
    )
    return await agent.handle_triage(triage_request)
