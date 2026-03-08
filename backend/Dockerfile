# ──────────────────────────────────────────────────────────────────────
#  TranscribeAI — Backend Dockerfile
#  Multi-stage build · Non-root user · Health check
# ──────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────
FROM python:3.10-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────
FROM python:3.10-slim

# System deps (ffmpeg for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Non-root user
RUN useradd --create-home appuser
WORKDIR /app

COPY . .
RUN mkdir -p temp_uploads temp_tts && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
