FROM python:3.11-slim

LABEL maintainer="CodeLens"
LABEL description="Repo-aware MCP server for semantic codebase search"
LABEL version="0.1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies for tree-sitter and sqlite-vec
# Also create a non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser

# Copy packaging files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Create directory for SQLite DB and logs, and set permissions
RUN mkdir -p logs data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Healthcheck to ensure process is alive
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import sqlite3; sqlite3.connect('codelens.sqlite').close()" || exit 1

ENTRYPOINT ["python", "-m", "codelens.server"]
