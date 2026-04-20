#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "Starting TranscribeAI..."

trap 'kill $(jobs -p) 2>/dev/null; exit' SIGINT SIGTERM

if [ -f "scripts/run_local.sh" ]; then
    bash scripts/run_local.sh &
else
    echo "scripts/run_local.sh not found"
fi

if [ -d "frontend" ]; then
    cd frontend && npm run dev &
    cd ..
else
    echo "frontend/ not found"
fi

echo "👉 Backend: http://localhost:8000"
echo "👉 Frontend: http://localhost:5173"

wait
