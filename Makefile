.PHONY: help install dev test lint format clean distclean run-podman

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies with uv"
	@echo "  make dev          - Install dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make distclean    - Clean build artifacts and remove virtual environment"
	@echo "  make run-podman   - Run container with podman (JOB=ecb|geonames|maxmind|ofcom)"

install:
	uv sync --no-dev

dev:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/

distclean: clean
	rm -rf .venv/

run-podman:
ifndef JOB
	$(error JOB is required. Usage: make run-podman JOB=ecb|geonames|maxmind|ofcom)
endif
	podman run --rm -p 8080:8080 \
		-e CRON_GCP_PROJECT_ID=${CRON_GCP_PROJECT_ID} \
		-e CRON_GCS_BUCKET=${CRON_GCS_BUCKET} \
		-e CRON_MAXMIND_LICENSE_KEY=${CRON_MAXMIND_LICENSE_KEY} \
		cron-services:latest $(JOB)



