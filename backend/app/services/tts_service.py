"""Text-to-Speech service using edge-tts."""

import asyncio
import logging
import os
import uuid

import edge_tts

from app.config import get_settings

logger = logging.getLogger("transcribeai.tts")
settings = get_settings()


async def list_voices(language: str | None = None) -> list[dict]:
    """Return available TTS voices, optionally filtered by language prefix."""
    all_voices = await edge_tts.list_voices()
    voices = []
    for v in all_voices:
        if language and not v["ShortName"].lower().startswith(language.lower()):
            continue
        voices.append(
            {
                "name": v["ShortName"],
                "gender": v["Gender"],
                "locale": v["Locale"],
            }
        )
    return voices


async def generate_speech(
    text: str,
    voice: str | None = None,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> str:
    """Generate an MP3 file from text and return its file path."""
    voice = voice or settings.TTS_DEFAULT_VOICE
    os.makedirs(settings.TTS_OUTPUT_DIR, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(settings.TTS_OUTPUT_DIR, filename)

    logger.info("TTS generate: voice=%s, chars=%d", voice, len(text))

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_path)

    logger.info("TTS saved: %s (%.1fKB)", output_path, os.path.getsize(output_path) / 1024)
    return output_path
