#!/bin/bash
set -e

# Script to run local CI checks before committing
# Mirrors .github/workflows/ci.yml

echo "--- Running Pre-commit Checks ---"

echo "[1/4] Syncing dependencies..."
uv sync --group dev

echo "[2/4] Checking formatting (ruff)..."
uv run ruff format --check

echo "[3/4] Linting (ruff)..."
uv run ruff check .

echo "[4/4] Running tests (pytest)..."
uv run pytest
