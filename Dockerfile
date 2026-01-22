# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .python-version ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src ./src
COPY geonames-urls.txt maxmind-urls.txt ofcom-urls.txt ./

# Install the project
RUN uv sync --frozen --no-dev


# Runtime stage
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/*.txt ./

# Set up environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app && \
    mkdir -p /tmp && \
    chown appuser:appuser /tmp

USER appuser

# Entry point for CLI
# Usage: podman run <image> ecb
# Or Cloud Run Job will pass job name as argument
ENTRYPOINT ["python", "-m", "src.cli"]
