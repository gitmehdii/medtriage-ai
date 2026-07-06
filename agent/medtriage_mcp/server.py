from typing import Any

from mcp.server.fastmcp import FastMCP

from medtriage_mcp.api_client import MedTriageApiClient
from medtriage_mcp.config import get_mcp_settings
from medtriage_mcp.tools import MedTriageTools


settings = get_mcp_settings()
api_client = MedTriageApiClient(
    base_url=settings.medtriage_agent_api_url,
    timeout_seconds=settings.medtriage_mcp_timeout_seconds,
)
tools = MedTriageTools(api_client)
mcp = FastMCP("MedTriageAI API")


@mcp.tool()
async def health_check() -> dict[str, Any]:
    """Check whether the MedTriage agent API is reachable."""
    return await tools.health_check()


@mcp.tool()
async def triage_patient(
    symptomes: str,
    age: int | None = None,
    sexe: str | None = None,
    antecedents: list[str] | None = None,
    medicaments: list[str] | None = None,
    allergies: list[str] | None = None,
    photo_base64: str | None = None,
) -> dict[str, Any]:
    """Run medical triage from symptom text and optional patient context."""
    return await tools.triage_patient(
        symptomes=symptomes,
        age=age,
        sexe=sexe,
        antecedents=antecedents,
        medicaments=medicaments,
        allergies=allergies,
        photo_base64=photo_base64,
    )


@mcp.tool()
async def chat_triage(
    message: str,
    conversation_id: str | None = None,
    history: list[dict[str, str]] | None = None,
    photo_base64: str | None = None,
) -> dict[str, Any]:
    """Continue a MedTriage conversation and return structured triage guidance."""
    return await tools.chat_triage(
        message=message,
        conversation_id=conversation_id,
        history=history,
        photo_base64=photo_base64,
    )


if __name__ == "__main__":
    mcp.run()
