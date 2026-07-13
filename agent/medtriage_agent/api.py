from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from medtriage_agent.config import Settings, get_settings
from medtriage_agent.conversation import InMemoryConversationStore
from medtriage_agent.llm import build_llm_provider
from medtriage_agent.module_clients import ExternalModuleClient
from medtriage_agent.ms_agent import MedTriageAgent, build_ms_agent_runtime
from medtriage_agent.orchestrator import TriageOrchestrator
from medtriage_agent.schemas import ChatRequest, TriageRequest, TriageResponse
from medtriage_mcp.knowledge_client import MedicalKnowledgeApiClient


def _build_knowledge_client(settings: Settings) -> MedicalKnowledgeApiClient | None:
    if not settings.medical_knowledge_service_url:
        return None
    return MedicalKnowledgeApiClient(
        base_url=settings.medical_knowledge_service_url,
        timeout_seconds=settings.medical_knowledge_timeout_seconds,
    )


settings = get_settings()
modules = ExternalModuleClient(settings)
llm = build_llm_provider(settings)
knowledge_client = _build_knowledge_client(settings)
orchestrator = TriageOrchestrator(
    modules=modules,
    llm=llm,
    knowledge_client=knowledge_client,
    knowledge_timeout_seconds=settings.medical_knowledge_timeout_seconds,
)
agent = build_ms_agent_runtime(MedTriageAgent(orchestrator))
conversation_store = InMemoryConversationStore(max_turns=settings.max_conversation_turns)

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
    conversation = conversation_store.get_or_create(request.conversation_id)
    conversation_store.record_user_reply(conversation.conversation_id, request.message)
    symptom_context = conversation_store.build_symptom_context(
        conversation=conversation,
        current_message=request.message,
        provided_history=request.history,
    )
    triage_request = TriageRequest(
        symptomes=symptom_context,
        photo_base64=request.photo_base64,
        conversation_id=conversation.conversation_id,
        answered_followups=sorted(conversation.answered_followups),
    )
    response = await agent.handle_triage(triage_request)
    conversation_store.add_turn(conversation.conversation_id, "user", request.message)
    conversation_store.add_turn(conversation.conversation_id, "assistant", response.message)
    conversation_store.set_pending_followups(
        conversation.conversation_id, response.questions_complementaires
    )
    return response
