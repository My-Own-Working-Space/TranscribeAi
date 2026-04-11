"""Application configuration via Pydantic Settings."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "TranscribeAI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MAX_FILE_SIZE_MB: int = 200
    SUPPORTED_FORMATS: list[str] = ["wav", "mp3", "flac", "ogg", "m4a", "mp4", "mkv", "webm"]

    WHISPER_MODEL: str = "base"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://transcribeai-iwaj.onrender.com",
        "https://transcribe-ai-six.vercel.app",
    ]

    TTS_DEFAULT_VOICE: str = "en-US-AriaNeural"
    TTS_OUTPUT_DIR: str = "temp_tts"

    REDIS_URL: str = ""

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""  # From Supabase Dashboard → Settings → API → JWT Secret
    DATABASE_URL: str = "sqlite:///./transcribe.db" # Updated in .env for Supabase Postgres

    model_config = {
        "env_file": os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            ".env",
        ),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
