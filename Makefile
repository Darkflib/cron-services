.PHONY: help install dev test lint format clean run-ecb run-geonames run-maxmind run-ofcom build-podman run-podman

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies with uv"
	@echo "  make dev          - Install dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make run-ecb      - Run ECB job locally"
	@echo "  make run-geonames - Run Geonames job locally"
	@echo "  make run-maxmind  - Run MaxMind job locally"
	@echo "  make run-ofcom    - Run Ofcom job locally"
	@echo "  make build-podman - Build container with podman"
	@echo "  make run-podman   - Run container with podman (JOB=ecb|geonames|maxmind|ofcom)"

install:
	uv sync --no-dev

dev:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check src/

format:
	uv run ruff format src/
	uv run ruff check --fix src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .venv/

run-ecb:
	uv run python -m src.main ecb

run-geonames:
	uv run python -m src.main geonames

run-maxmind:
	uv run python -m src.main maxmind

run-ofcom:
	uv run python -m src.main ofcom

build-podman:
	podman build -t cron-services:latest .

run-podman:
	podman run --rm -p 8080:8080 \
		-e CRON_GCP_PROJECT_ID=${CRON_GCP_PROJECT_ID} \
		-e CRON_GCS_BUCKET=${CRON_GCS_BUCKET} \
		-e CRON_MAXMIND_LICENSE_KEY=${CRON_MAXMIND_LICENSE_KEY} \
		cron-services:latest $(JOB)
