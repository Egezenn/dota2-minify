#!/bin/bash
set -e

# Script to run local CI checks before committing
# Mirrors .github/workflows/ci.yml

echo "--- Running Pre-commit Checks ---"

echo "[1/5] Syncing dependencies..."
uv sync --group dev

echo "[2/5] Checking formatting (ruff)..."
uv run ruff format Minify tests --check

echo "[3/5] Linting (ruff)..."
uv run ruff check Minify tests

echo "[4/5] Running tests (pytest)..."
uv run pytest

echo "[5/5] Cleaning up logs..."
rm -f Minify/logs/warnings.txt
