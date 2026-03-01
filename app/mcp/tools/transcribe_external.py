"""External API transcription agent.

This agent delegates transcription to external cloud APIs (OpenAI, Groq)
for comparison, fallback, or when local resources are insufficient.
"""

import asyncio
import logging
import os
import tempfile
from typing import Any, Literal

import httpx

from app.config import settings
from app.mcp.base_agent import BaseTranscriptionAgent
from app.schemas import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)

Provider = Literal["openai", "groq"]


class ExternalAPIAgent(BaseTranscriptionAgent):
    """Transcription agent using external cloud APIs."""

    def __init__(
        self,
        provider: Provider = "groq",
        api_key: str | None = None,
    ) -> None:
        """Initialize the external API agent.

        Args:
            provider: API provider (openai, groq).
            api_key: API key. Falls back to config/environment.
        """
        self._provider = provider
        self._api_key = api_key or self._get_api_key()
        self._client: httpx.AsyncClient | None = None

    def _get_api_key(self) -> str | None:
        """Get API key from config or environment."""
        if self._provider == "groq":
            return settings.groq_api_key or os.getenv("GROQ_API_KEY")
        elif self._provider == "openai":
            return settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        return None

    @property
    def name(self) -> str:
        """Agent name."""
        return f"external_{self._provider}"

    @property
    def description(self) -> str:
        """Agent description."""
        return f"External transcription via {self._provider.upper()} API"

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=300.0)
        return self._client

    async def _transcribe_openai(
        self,
        audio_data: bytes,
        language: str | None,
        prompt: str | None = None,
    ) -> TranscriptResult:
        """Transcribe using OpenAI Whisper API."""
        client = await self._ensure_client()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            data_payload = {
                "model": "whisper-1",
                "response_format": "verbose_json",
                "language": language or "",
            }
            if prompt:
                data_payload["prompt"] = prompt

            with open(temp_path, "rb") as audio_file:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    files={"file": ("audio.wav", audio_file, "audio/wav")},
                    data=data_payload,
                )

            response.raise_for_status()
            data = response.json()

            segments: list[TranscriptSegment] = []
            for seg in data.get("segments", []):
                segments.append(
                    TranscriptSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"].strip(),
                        confidence=seg.get("avg_logprob", 0) + 1.0,
                        speaker=None,
                    )
                )

            return TranscriptResult(
                agent_name=self.name,
                language=data.get("language", "unknown"),
                segments=segments,
                avg_confidence=0.9,  # OpenAI doesn't provide overall confidence
                meta={
                    "provider": "openai",
                    "model": "whisper-1",
                    "duration": data.get("duration"),
                },
            )

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def _transcribe_groq(
        self,
        audio_data: bytes,
        language: str | None,
        prompt: str | None = None,
    ) -> TranscriptResult:
        """Transcribe using Groq Whisper API."""
        client = await self._ensure_client()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            data_payload = {
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
                "language": language or "",
            }
            if prompt:
                data_payload["prompt"] = prompt

            with open(temp_path, "rb") as audio_file:
                response = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    files={"file": ("audio.wav", audio_file, "audio/wav")},
                    data=data_payload,
                )

            response.raise_for_status()
            data = response.json()

            segments: list[TranscriptSegment] = []
            for seg in data.get("segments", []):
                segments.append(
                    TranscriptSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"].strip(),
                        confidence=0.9,
                        speaker=None,
                    )
                )

            return TranscriptResult(
                agent_name=self.name,
                language=data.get("language", "unknown"),
                segments=segments,
                avg_confidence=0.9,
                meta={
                    "provider": "groq",
                    "model": "whisper-large-v3",
                    "duration": data.get("duration"),
                },
            )

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs: Any,
    ) -> TranscriptResult:
        """Transcribe audio using external API.

        Args:
            audio_data: Raw audio bytes.
            language: Optional ISO language code.
            **kwargs: Additional provider-specific options (context).

        Returns:
            TranscriptResult: Transcription result from external API.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self._api_key:
            raise ValueError(f"API key not configured for {self._provider}")

        # Build prompt from context
        prompt = None
        if context := kwargs.get("context"):
            parts = []
            if vocab := context.get("vocabulary"):
                if isinstance(vocab, list):
                    parts.append(", ".join(vocab))
                else:
                    parts.append(str(vocab))
            if custom_prompt := context.get("prompt"):
                parts.append(custom_prompt)
            if parts:
                prompt = " ".join(parts)
                logger.info(f"External API using prompt: {prompt[:100]}...")

        if self._provider == "openai":
            return await self._transcribe_openai(audio_data, language, prompt)
        elif self._provider == "groq":
            return await self._transcribe_groq(audio_data, language, prompt)
        else:
            raise ValueError(f"Unsupported provider: {self._provider}")

    async def health_check(self) -> bool:
        """Check if API is accessible."""
        if not self._api_key:
            logger.warning(f"No API key for {self._provider}")
            return False
        return True

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()


def create_agent(
    provider: Provider | None = None,
    api_key: str | None = None,
) -> ExternalAPIAgent:
    """Create an ExternalAPIAgent with environment defaults."""
    return ExternalAPIAgent(
        provider=provider or os.getenv("EXTERNAL_PROVIDER", "groq"),  # type: ignore
        api_key=api_key,
    )
