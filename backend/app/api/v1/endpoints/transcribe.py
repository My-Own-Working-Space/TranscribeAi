"""V1 transcription endpoints."""

import logging
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel
from typing import Optional, List

from app.config import get_settings
from app.services.transcription_service import transcription_service

logger = logging.getLogger("transcribeai.api.transcribe")
settings = get_settings()
router = APIRouter()

jobs: dict = {}


class TranscriptionResponse(BaseModel):
    job_id: str
    status: str


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    confidence: float = 0.0


class FullTranscriptionResponse(BaseModel):
    transcript: str
    confidence: float
    segments: List[TranscriptSegment]
    processing_time_s: float = 0.0
    file_size_bytes: int = 0
    model: str = ""
    language_detected: str = ""


ALLOWED_EXTENSIONS = {f".{fmt}" for fmt in settings.SUPPORTED_FORMATS}


def _validate_file(upload: UploadFile) -> None:
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


from app.models import User
from app.api.v2.endpoints.auth import get_current_user
from fastapi import Depends

@router.post("/", response_model=TranscriptionResponse)
async def transcribe_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Upload an audio/video file and start transcription."""
    _validate_file(file)

    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)

    job_id = str(uuid.uuid4())
    safe_name = f"{job_id}_{os.path.basename(file.filename or 'upload')}"
    file_path = os.path.join(temp_dir, safe_name)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    total_written = 0

    try:
        with open(file_path, "wb") as buf:
            while chunk := await file.read(256 * 1024):
                total_written += len(chunk)
                if total_written > max_bytes:
                    buf.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.",
                    )
                buf.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("File save failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # ─── SEC: Link job to user_id (IDOR prevention) ───
    jobs[job_id] = {
        "status": "processing", 
        "result": None, 
        "error": None,
        "user_id": current_user.id
    }

    logger.info("Job %s created by %s (file=%s)", job_id, current_user.id, file.filename)

    background_tasks.add_task(
        transcription_service.process_transcription,
        job_id=job_id,
        file_path=file_path,
        language=language,
        jobs_dict=jobs,
    )

    return {"job_id": job_id, "status": "processing"}


@router.get("/status/{job_id}")
async def get_status(job_id: str, current_user: User = Depends(get_current_user)):
    """Poll transcription job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # ─── SEC: Check ownership ───
    if jobs[job_id].get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to see this job")
        
    return jobs[job_id]
