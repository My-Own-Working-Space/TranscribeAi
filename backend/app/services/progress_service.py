"""Job progress tracking via Redis — provides real-time progress to frontend."""

import json
import logging
import redis
from app.config import get_settings

logger = logging.getLogger("transcribeai.progress")
settings = get_settings()

PROGRESS_TTL = 600  # 10 minutes — auto-cleanup after job completes

_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3)
    return _redis_client


def _key(job_id: str) -> str:
    return f"progress:{job_id}"


def set_progress(job_id: str, percent: int, step: str, detail: str = ""):
    """Update job progress in Redis."""
    try:
        r = _get_redis()
        data = json.dumps({
            "percent": min(percent, 100),
            "step": step,
            "detail": detail,
        }, ensure_ascii=False)
        r.setex(_key(job_id), PROGRESS_TTL, data)
    except Exception as e:
        logger.debug("Progress update failed: %s", e)


def get_progress(job_id: str) -> dict:
    """Read current progress for a job."""
    try:
        r = _get_redis()
        raw = r.get(_key(job_id))
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.debug("Progress read failed: %s", e)
    return {"percent": 0, "step": "queued", "detail": ""}


def clear_progress(job_id: str):
    """Remove progress key after job completes."""
    try:
        r = _get_redis()
        r.delete(_key(job_id))
    except Exception:
        pass
