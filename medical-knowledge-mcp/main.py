import logging

import uvicorn

from medical_knowledge_mcp.config import get_settings


def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    uvicorn.run("medical_knowledge_mcp.api:app", host="0.0.0.0", port=settings.port)


if __name__ == "__main__":
    main()
