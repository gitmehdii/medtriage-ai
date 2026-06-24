import uvicorn

from medtriage_agent.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "medtriage_agent.api:app",
        host="0.0.0.0",
        port=settings.agent_port,
        reload=settings.app_env == "local",
    )


if __name__ == "__main__":
    main()
