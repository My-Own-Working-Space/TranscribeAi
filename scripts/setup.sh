#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Installing Python dependencies..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo "Installing frontend dependencies..."
cd frontend && npm install
cd ..

echo ""
echo "Setup complete!"
echo ""
echo "Run:  ./scripts/dev.sh"
