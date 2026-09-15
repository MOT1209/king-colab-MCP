FROM python:3.11-slim

RUN groupadd -r mcp && useradd -r -g mcp -d /app mcp

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

RUN mkdir -p /app/workspace /app/logs && chown -R mcp:mcp /app

USER mcp

ENV MCP_TRANSPORT=stdio \
    LOG_LEVEL=INFO \
    COLAB_WORKSPACE_ROOT=/app/workspace \
    COLAB_ARTIFACT_ROOT=/app/workspace/artifacts \
    COLAB_NOTEBOOK_ROOT=/app/workspace/notebooks \
    AUDIT_LOG_PATH=/app/logs/audit.log

EXPOSE 8765

ENTRYPOINT ["google-colab-mcp"]
