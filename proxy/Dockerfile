# Build from project root:  docker build -f proxy/Dockerfile -t mcp-gateway .
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY proxy/ ./proxy/
COPY observability/ ./observability/
COPY agents/__init__.py ./agents/__init__.py
COPY agents/validation.py ./agents/validation.py

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "proxy.mcp_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
