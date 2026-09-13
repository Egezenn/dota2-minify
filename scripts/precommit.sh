#!/bin/bash
set -e

# Script to run local CI checks before committing
# Mirrors .github/workflows/ci.yml

echo "--- Running Pre-commit Checks ---"

echo "[1/8] Syncing dependencies..."
uv sync --group dev

echo "[2/8] Checking Python formatting (ruff)..."
uv run ruff format Minify tests --check

echo "[3/8] Checking Web formatting (prettier)..."
npx --yes -p prettier -p prettier-plugin-svelte@3 bash -c "prettier --plugin=\$(dirname \$(which prettier))/../prettier-plugin-svelte/plugin.js --check \"Minify/**/*.{svelte,ts,js,css,json,html}\""

echo "[4/8] Type-checking TypeScript (tsc)..."
npx --yes -p typescript tsc --project Minify/ui/web/tsconfig.json --noEmit
npx --yes -p typescript tsc --project Minify/plugins/tsconfig.json --noEmit

echo "[5/8] Checking Svelte components (svelte-check)..."
npx --yes svelte-check@3 --tsconfig Minify/ui/web/tsconfig.json
npx --yes svelte-check@3 --tsconfig Minify/plugins/tsconfig.json

echo "[6/8] Linting Python (ruff)..."
uv run ruff check Minify tests

echo "[7/8] Running tests (pytest)..."
uv run pytest

echo "[8/8] Cleaning up logs..."
rm -f Minify/logs/warnings.txt
