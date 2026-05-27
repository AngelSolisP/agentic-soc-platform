FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy A2A gateway
COPY a2a_gateway/ ./a2a_gateway/

# Copy agent stack (needed for orchestrator)
COPY agents/ ./agents/
COPY runbooks/ ./runbooks/
COPY config/ ./config/
COPY observability/ ./observability/

# Copy auth middleware (shared with MCP Gateway)
COPY proxy/__init__.py ./proxy/__init__.py
COPY proxy/mcp_gateway/__init__.py ./proxy/mcp_gateway/__init__.py
COPY proxy/mcp_gateway/auth_middleware.py ./proxy/mcp_gateway/auth_middleware.py

# Non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "a2a_gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
