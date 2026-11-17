#!/bin/bash
set -e
cd "$(dirname "$0")"
PYTHON="${AGRI_PYTHON:-python3}"
"$PYTHON" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM
npm run dev --prefix frontend -- --host 127.0.0.1 --port 5174 --strictPort
