# ──────────────────────────────────────────────────────────────────────
#  TranscribeAI — Backend Dockerfile
#  Single-stage build for Render compatibility
# ──────────────────────────────────────────────────────────────────────

FROM python:3.10-slim

# System deps (build tools for whisper + runtime deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential python3-dev git \
    rustc cargo pkg-config libssl-dev \
    ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    torch==2.1.2+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html && \
    pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .
RUN mkdir -p temp_uploads temp_tts

# Non-root user
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
