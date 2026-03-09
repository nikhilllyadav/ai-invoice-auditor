#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Cleaning runtime data (safe reset)..."

# Keep logger module; clear only log files.
find logs -type f ! -name "logger_module.py" -delete 2>/dev/null || true

# Clear caches
rm -rf __pycache__ agents/__pycache__ agents/rag_agents/__pycache__ ui/__pycache__ 2>/dev/null || true

# Clear data artifacts
rm -f data/incoming/* 2>/dev/null || true
rm -f data/reports/* 2>/dev/null || true
rm -f data/kb/faiss_new/* 2>/dev/null || true
rm -f checkpoints.sqlite 2>/dev/null || true

echo "Done."
