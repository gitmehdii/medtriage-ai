from typing import Any

from mcp.server.fastmcp import FastMCP

from medical_knowledge_mcp.service import MedicalKnowledgeService
from medical_knowledge_mcp.tools import MedicalKnowledgeTools


service = MedicalKnowledgeService()
tools = MedicalKnowledgeTools(service)
mcp = FastMCP("Medical Knowledge MCP")


@mcp.tool()
def search_medical_guidelines(query: str, speciality: str | None = None, country: str = "FR", limit: int = 5) -> dict[str, Any]:
    """Search validated medical guidelines and return citations with publication, update, verification, and retrieval dates."""
    return tools.search_medical_guidelines(query, speciality, country, limit)


@mcp.tool()
def get_red_flags(symptom: str, country: str = "FR") -> dict[str, Any]:
    """Get validated red flags with citations and publication, update, verification, and retrieval dates."""
    return tools.get_red_flags(symptom, country)


@mcp.tool()
def get_source_details(source_id: str) -> dict[str, Any]:
    """Get source metadata including citation, publication, update, verification, and retrieval dates."""
    return tools.get_source_details(source_id)


if __name__ == "__main__":
    mcp.run()
