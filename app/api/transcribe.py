"""Transcription API endpoints.

This module defines the REST API endpoints for audio transcription,
including file upload, URL download, and result retrieval.
"""

import logging
import tempfile
import uuid
from typing import Literal
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl

from app.mcp.orchestrator import get_orchestrator, setup_default_agents
from app.mcp.tools.merge_transcript import MergeStrategy
from app.schemas import FinalTranscript
from app.services.audio_loader import get_audio_loader
from app.services.cache import get_cache
from app.services.post_processor import get_post_processor

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job storage (use Redis/DB in production)
_jobs: dict[str, dict] = {}


class TranscribeResponse(BaseModel):
    """Response model for transcription requests."""

    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    transcript: FinalTranscript | None = None
    error: str | None = None


class TranscribeUrlRequest(BaseModel):
    """Request model for URL-based transcription."""

    url: HttpUrl
    language: str | None = None
    agents: str | None = None
    strategy: MergeStrategy = "confidence"
    prompt: str | None = None
    vocabulary: str | None = None
    auto_correct: bool = True  # Auto-correct transcription errors with LLM
    fast_mode: bool = False  # Use only fastest agent
    use_cache: bool = True  # Cache results


class HealthResponse(BaseModel):
    """Response model for agent health check."""

    agents: dict[str, bool]
    total: int
    healthy: int


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Form(default=None),
    agents: str | None = Form(default=None),
    strategy: MergeStrategy = Form(default="confidence"),
    prompt: str | None = Form(default=None),
    vocabulary: str | None = Form(default=None),
    auto_correct: bool = Form(default=True),
    fast_mode: bool = Form(default=False),
    use_cache: bool = Form(default=True),
) -> TranscribeResponse:
    """Transcribe an uploaded audio file using multi-agent system.

    Args:
        file: Audio file upload.
        language: ISO language code (e.g., 'en', 'vi'). None for auto-detect.
        agents: Comma-separated agent names to use. None for all.
        strategy: Merge strategy (confidence, longest, first).
        prompt: Initial prompt to guide transcription (e.g., "This is a programming tutorial").
        vocabulary: Comma-separated vocabulary hints (e.g., "ASP.NET, MVC, Entity Framework").
        auto_correct: Auto-correct transcription errors using LLM (default: True).
        fast_mode: Use only fastest agent for speed (default: False).
        use_cache: Use cached results if available (default: True).

    Returns:
        TranscribeResponse: Transcription result.
    """
    job_id = str(uuid.uuid4())[:8]
    logger.info(f"Job {job_id}: Starting transcription for {file.filename}")

    try:
        # Load audio
        audio_loader = get_audio_loader()
        audio_data = await audio_loader.load_stream(file.file, file.filename or "")

        # Get orchestrator
        orchestrator = get_orchestrator()

        # Ensure agents are registered
        if not orchestrator.agents:
            await setup_default_agents(orchestrator)

        # Parse agent list
        agent_list = None
        if agents:
            agent_list = [a.strip() for a in agents.split(",")]

        # Build context for vocabulary hints
        context = {}
        if prompt:
            context["prompt"] = prompt
        if vocabulary:
            context["vocabulary"] = [v.strip() for v in vocabulary.split(",")]

        # Run transcription with optimizations
        transcript = await orchestrator.transcribe(
            audio_data=audio_data,
            language=language,
            agents=agent_list,
            merge_strategy=strategy,
            fast_mode=fast_mode,
            use_cache=use_cache,
            context=context if context else None,
        )

        # Apply post-processing if enabled (skip in fast_mode for speed)
        if auto_correct and not fast_mode:
            post_processor = get_post_processor()
            transcript = await post_processor.process_transcript(transcript, use_llm=True)
            logger.info(f"Job {job_id}: Post-processing applied")

        logger.info(
            f"Job {job_id}: Completed with {len(transcript.segments)} segments"
        )

        return TranscribeResponse(
            job_id=job_id,
            status="completed",
            transcript=transcript,
        )

    except ValueError as e:
        logger.warning(f"Job {job_id}: Validation error - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe/path", response_model=TranscribeResponse)
async def transcribe_from_path(
    audio_path: str,
    language: str | None = None,
    agents: str | None = None,
    strategy: MergeStrategy = "confidence",
) -> TranscribeResponse:
    """Transcribe an audio file from a local path.

    Args:
        audio_path: Absolute path to audio file on server.
        language: ISO language code. None for auto-detect.
        agents: Comma-separated agent names.
        strategy: Merge strategy.

    Returns:
        TranscribeResponse: Transcription result.
    """
    job_id = str(uuid.uuid4())[:8]
    logger.info(f"Job {job_id}: Transcribing from path {audio_path}")

    try:
        orchestrator = get_orchestrator()

        if not orchestrator.agents:
            await setup_default_agents(orchestrator)

        agent_list = [a.strip() for a in agents.split(",")] if agents else None

        transcript = await orchestrator.transcribe(
            audio_path=audio_path,
            language=language,
            agents=agent_list,
            merge_strategy=strategy,
        )

        return TranscribeResponse(
            job_id=job_id,
            status="completed",
            transcript=transcript,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe/url", response_model=TranscribeResponse)
async def transcribe_from_url(
    request: TranscribeUrlRequest,
) -> TranscribeResponse:
    """Transcribe audio/video from a URL.

    Downloads the file from URL and transcribes it.
    Supports direct links to audio/video files.

    Args:
        request: URL and transcription options.

    Returns:
        TranscribeResponse: Transcription result.
    """
    job_id = str(uuid.uuid4())[:8]
    url_str = str(request.url)
    logger.info(f"Job {job_id}: Transcribing from URL {url_str}")

    try:
        # Extract filename from URL
        parsed = urlparse(url_str)
        filename = parsed.path.split("/")[-1] or "audio"

        # Download file
        logger.info(f"Job {job_id}: Downloading from {url_str}...")
        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            response = await client.get(url_str)
            response.raise_for_status()
            audio_data = response.content

        logger.info(f"Job {job_id}: Downloaded {len(audio_data) / 1024:.1f}KB")

        # Validate format from filename or content-type
        content_type = response.headers.get("content-type", "")
        if not filename or "." not in filename:
            # Try to get extension from content-type
            ext_map = {
                "audio/wav": ".wav",
                "audio/x-wav": ".wav",
                "audio/mpeg": ".mp3",
                "audio/mp3": ".mp3",
                "audio/mp4": ".m4a",
                "audio/m4a": ".m4a",
                "audio/flac": ".flac",
                "audio/ogg": ".ogg",
                "video/mp4": ".mp4",
                "video/webm": ".webm",
                "video/x-matroska": ".mkv",
            }
            ext = ext_map.get(content_type.split(";")[0], ".wav")
            filename = f"audio{ext}"

        # Get orchestrator
        orchestrator = get_orchestrator()

        if not orchestrator.agents:
            await setup_default_agents(orchestrator)

        # Parse agent list
        agent_list = None
        if request.agents:
            agent_list = [a.strip() for a in request.agents.split(",")]

        # Build context for vocabulary hints
        context = {}
        if request.prompt:
            context["prompt"] = request.prompt
        if request.vocabulary:
            context["vocabulary"] = [v.strip() for v in request.vocabulary.split(",")]

        # Run transcription with optimizations
        transcript = await orchestrator.transcribe(
            audio_data=audio_data,
            language=request.language,
            agents=agent_list,
            merge_strategy=request.strategy,
            fast_mode=request.fast_mode,
            use_cache=request.use_cache,
            context=context if context else None,
        )

        # Apply post-processing if enabled (skip in fast_mode for speed)
        if request.auto_correct and not request.fast_mode:
            post_processor = get_post_processor()
            transcript = await post_processor.process_transcript(transcript, use_llm=True)
            logger.info(f"Job {job_id}: Post-processing applied")

        logger.info(
            f"Job {job_id}: Completed with {len(transcript.segments)} segments"
        )

        return TranscribeResponse(
            job_id=job_id,
            status="completed",
            transcript=transcript,
        )

    except httpx.HTTPStatusError as e:
        logger.error(f"Job {job_id}: Failed to download - {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download file: {e.response.status_code}",
        )
    except httpx.RequestError as e:
        logger.error(f"Job {job_id}: Network error - {e}")
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Job {job_id}: Failed - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=HealthResponse)
async def get_agents_health() -> HealthResponse:
    """Get health status of all registered transcription agents.

    Returns:
        HealthResponse: Agent health status.
    """
    orchestrator = get_orchestrator()

    if not orchestrator.agents:
        await setup_default_agents(orchestrator)

    health = await orchestrator.health_check()

    return HealthResponse(
        agents=health,
        total=len(health),
        healthy=sum(1 for v in health.values() if v),
    )


@router.get("/agents/list")
async def list_agents() -> dict:
    """List all registered agents with their descriptions.

    Returns:
        dict: Agent information.
    """
    orchestrator = get_orchestrator()

    if not orchestrator.agents:
        await setup_default_agents(orchestrator)

    agents_info = []
    for name in orchestrator.agents:
        agent = orchestrator._agents[name]
        agents_info.append({
            "name": name,
            "description": agent.description,
        })

    return {"agents": agents_info, "count": len(agents_info)}


@router.get("/cache/stats")
async def get_cache_stats() -> dict:
    """Get cache statistics.

    Returns:
        dict: Cache stats including size, hits, misses, hit_rate.
    """
    cache = get_cache()
    return cache.stats


@router.delete("/cache/clear")
async def clear_cache() -> dict:
    """Clear all cached transcriptions.

    Returns:
        dict: Number of entries cleared.
    """
    cache = get_cache()
    count = cache.clear()
    return {"cleared": count, "message": f"Cleared {count} cached entries"}
