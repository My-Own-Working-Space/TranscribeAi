"""Application configuration settings.

This module defines all configuration parameters using Pydantic settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TranscribeAI"
    debug: bool = False
    log_level: str = "INFO"

    # Audio processing
    max_audio_size_mb: int = 100
    # Use str for env compat, parse in code when needed
    supported_formats_str: str = "wav,mp3,flac,ogg,m4a"

    # MCP orchestrator
    default_timeout_seconds: float = 300.0
    max_concurrent_agents: int = 3

    # Whisper model
    whisper_model_size: str = "small"
    whisper_device: str = "auto"
    whisper_compute_type: str = "int8"

    # Storage
    storage_backend: str = "local"
    redis_url: str | None = None

    # External APIs
    groq_api_key: str | None = None
    openai_api_key: str | None = None

    @property
    def supported_formats(self) -> list[str]:
        """Parse comma-separated formats string to list."""
        return [f.strip() for f in self.supported_formats_str.split(",") if f.strip()]


settings = Settings()
