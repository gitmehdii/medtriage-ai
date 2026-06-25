import logging

import uvicorn

from medtriage_agent.config import get_settings


def main() -> None:
    settings = get_settings()
    log_level = logging.DEBUG if settings.app_env == "local" else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    uvicorn.run(
        "medtriage_agent.api:app",
        host="0.0.0.0",
        port=settings.agent_port,
        reload=settings.app_env == "local",
    )


if __name__ == "__main__":
    main()
