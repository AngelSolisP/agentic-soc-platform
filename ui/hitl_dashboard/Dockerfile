# Build from project root:  docker build -f ui/hitl_dashboard/Dockerfile -t hitl-backend .
FROM python:3.11-slim

WORKDIR /app

# Install dependencies from project requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ui/ ./ui/
COPY observability/ ./observability/
COPY proxy/__init__.py ./proxy/__init__.py
COPY proxy/mcp_gateway/__init__.py ./proxy/mcp_gateway/__init__.py
COPY proxy/mcp_gateway/auth_middleware.py ./proxy/mcp_gateway/auth_middleware.py

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8081
EXPOSE 8081

CMD ["uvicorn", "ui.hitl_dashboard.backend.main:app", "--host", "0.0.0.0", "--port", "8081"]
