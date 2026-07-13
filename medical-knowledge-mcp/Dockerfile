FROM python:3.11-slim

WORKDIR /app

COPY medical-knowledge-mcp/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/medical_knowledge_mcp ./medical_knowledge_mcp
COPY medical-knowledge-mcp/main.py ./main.py

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["python", "main.py"]
