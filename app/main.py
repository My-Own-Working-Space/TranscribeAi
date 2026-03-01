"""FastAPI application entry point for TranscribeAI.

This module initializes the FastAPI application and registers all routes.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import transcribe
from app.config import settings
from app.mcp.orchestrator import get_orchestrator, setup_default_agents

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info(f"Starting {settings.app_name}...")

    # Initialize orchestrator with default agents
    orchestrator = get_orchestrator()
    await setup_default_agents(orchestrator)
    logger.info(f"Registered agents: {orchestrator.agents}")

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="Multi-agent speech-to-text transcription service",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(transcribe.router, prefix="/api/v1", tags=["transcription"])


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    orchestrator = get_orchestrator()
    agent_health = await orchestrator.health_check()

    return {
        "status": "ok",
        "app": settings.app_name,
        "agents": {
            "registered": len(agent_health),
            "healthy": sum(1 for v in agent_health.values() if v),
        },
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint with API info."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "transcribe": "/api/v1/transcribe",
    }
