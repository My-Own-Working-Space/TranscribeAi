#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${GREEN}[dev]${NC} $*"; }

if [ ! -d ".venv" ]; then
    info "Creating .venv..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

if [ -f .env ]; then
    set -a; source .env; set +a
    info "Loaded .env"
fi

if [ ! -d "frontend/node_modules" ]; then
    info "Installing frontend deps..."
    (cd frontend && npm install)
fi

info "Starting backend on :${PORT:-8000}"
info "Starting frontend on :5173"
echo ""

trap 'kill 0; exit' SIGINT SIGTERM

.venv/bin/python -m uvicorn app.main:app \
    --host "${HOST:-0.0.0.0}" \
    --port "${PORT:-8000}" \
    --reload \
    --app-dir backend &

(cd frontend && npm run dev -- --host) &

wait
