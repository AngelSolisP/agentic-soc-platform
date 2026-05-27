# workbench/Dockerfile
# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY workbench/frontend/package.json workbench/frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY workbench/frontend/ ./
RUN npm run build

# Stage 2: Python backend + static frontend
# Python 3.12 required: fixes anyio CancelScope cross-task bug that kills
# MCP sessions after sub-agent completion (Python 3.11 + anyio incompatibility).
FROM python:3.12-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY workbench/ ./workbench/
COPY agents/ ./agents/
COPY runbooks/ ./runbooks/
COPY config/ ./config/
COPY observability/ ./observability/
COPY proxy/mcp_gateway/auth_middleware.py ./proxy/mcp_gateway/auth_middleware.py
COPY proxy/__init__.py ./proxy/__init__.py
COPY proxy/mcp_gateway/__init__.py ./proxy/mcp_gateway/__init__.py

# Copy built frontend into backend serving directory
COPY --from=frontend-build /app/frontend/dist ./workbench/frontend/dist/

# Security: non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8083
EXPOSE 8083

# Shell form so $PORT is expanded at runtime (Cloud Run injects PORT env var)
CMD uvicorn workbench.backend.main:app --host 0.0.0.0 --port ${PORT:-8083}
