#!/bin/bash
# Run TranscribeAI locally for development

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Default values
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-true}"

echo "🚀 Starting TranscribeAI server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Reload: $RELOAD"

# Use virtual environment
PYTHON=".venv/bin/python"
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Run with uvicorn
if [ "$RELOAD" = "true" ]; then
    $PYTHON -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
    $PYTHON -m uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
