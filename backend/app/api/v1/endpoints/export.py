"""Export endpoints — download transcription results as SRT, TXT, or JSON."""

import json
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response

from app.api.v1.endpoints.transcribe import jobs
from app.services.srt_service import segments_to_srt

logger = logging.getLogger("transcribeai.api.export")
router = APIRouter()


@router.get("/{job_id}")
async def export_transcription(
    job_id: str,
    format: str = Query("srt", enum=["srt", "txt", "json"]),
):
    """Download transcription result in the specified format.

    - **srt**: SubRip subtitle file (.srt)
    - **txt**: Plain text transcript
    - **json**: Full result with segments and metadata
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Job is not completed yet (status: {job['status']})",
        )

    result = job["result"]

    if format == "srt":
        srt_content = segments_to_srt(result.get("segments", []))
        return Response(
            content=srt_content,
            media_type="application/x-subrip",
            headers={"Content-Disposition": f'attachment; filename="{job_id}.srt"'},
        )

    elif format == "txt":
        return PlainTextResponse(
            content=result.get("transcript", ""),
            headers={"Content-Disposition": f'attachment; filename="{job_id}.txt"'},
        )

    elif format == "json":
        return Response(
            content=json.dumps(result, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{job_id}.json"'},
        )
