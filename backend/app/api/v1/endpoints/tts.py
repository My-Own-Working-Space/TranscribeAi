"""Text-to-Speech API endpoints."""

import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.tts_service import generate_speech, list_voices

logger = logging.getLogger("transcribeai.api.tts")
router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: str | None = Field(None, description="Voice name, e.g. 'vi-VN-HoaiMyNeural'")
    rate: str = Field("+0%", description="Speaking rate adjustment, e.g. '+20%' or '-10%'")
    pitch: str = Field("+0Hz", description="Pitch adjustment, e.g. '+5Hz'")


class TTSResponse(BaseModel):
    audio_url: str
    voice_used: str
    text_length: int


@router.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """Generate speech audio from text.

    Returns a URL to download the generated MP3 file.
    """
    try:
        file_path = await generate_speech(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
        )

        filename = os.path.basename(file_path)
        return TTSResponse(
            audio_url=f"/api/v1/tts/audio/{filename}",
            voice_used=request.voice or "en-US-AriaNeural",
            text_length=len(request.text),
        )
    except Exception as e:
        logger.error("TTS generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """Download generated TTS audio file."""
    # ─── SEC: Path Traversal Fix ───
    safe_filename = os.path.basename(filename)
    file_path = os.path.abspath(os.path.join("temp_tts", safe_filename))
    
    # Ensure it's inside the temp_tts directory
    base_dir = os.path.abspath("temp_tts")
    if not file_path.startswith(base_dir) or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=safe_filename,
    )


@router.get("/voices")
async def get_voices(language: str | None = None):
    """List available TTS voices, optionally filtered by language code (e.g. 'vi', 'en')."""
    voices = await list_voices(language)
    return {"voices": voices, "count": len(voices)}
