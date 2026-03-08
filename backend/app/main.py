"""TranscribeAI — FastAPI application entry point."""

import logging
import sys
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.api.v2 import v2_router
from app.config import get_settings
from app.database import init_db

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("transcribeai")

_start_time = time.time()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Meeting & Lecture Assistant — transcription, AI summary, chat Q&A, and more.",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ─── Security Headers Middleware ───
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://*.supabase.co;"
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Restricted CORS - Don't allow '*' with credentials
origins = settings.ALLOWED_ORIGINS
if "*" in origins:
    logger.warning("Wildcard CORS detected. In production, this should be restricted.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s → %s (%.0fms)", request.method, request.url.path, response.status_code, ms)
    return response


@app.exception_handler(413)
async def file_too_large(_request: Request, _exc):
    return JSONResponse(status_code=413, content={
        "error": "file_too_large",
        "detail": f"File exceeds the {settings.MAX_FILE_SIZE_MB}MB limit.",
    })


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"error": "internal_error", "detail": "An internal error occurred."})


app.include_router(api_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")


@app.get("/health", tags=["system"])
async def health_check(request: Request):
    # Basic check for everyone
    status = {"status": "healthy"}
    
    # Detailed check only for local or potentially authenticated admins later
    if settings.DEBUG or request.client.host == "127.0.0.1":
        status.update({
            "version": settings.APP_VERSION,
            "uptime_seconds": int(time.time() - _start_time),
            "model": settings.WHISPER_MODEL,
            "ai_features": bool(settings.GROQ_API_KEY),
        })
    return status


@app.on_event("startup")
async def on_startup():
    init_db()
    logger.info(
        "🚀 %s v%s (model=%s, ai=%s)",
        settings.APP_NAME, settings.APP_VERSION, settings.WHISPER_MODEL,
        "on" if settings.GROQ_API_KEY else "off",
    )


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 %s shutting down", settings.APP_NAME)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
