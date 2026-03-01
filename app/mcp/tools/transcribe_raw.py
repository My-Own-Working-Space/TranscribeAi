"""Raw transcription agent using local Whisper model.

This agent performs transcription using faster-whisper library locally,
inspired by the WhisperAi project implementation.
"""

import asyncio
import logging
import os
import tempfile
from typing import Any

from app.mcp.base_agent import BaseTranscriptionAgent
from app.schemas import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class WhisperRawAgent(BaseTranscriptionAgent):
    """Local Whisper transcription agent using faster-whisper."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "int8",
    ) -> None:
        """Initialize the Whisper agent.

        Args:
            model_size: Model size (tiny, base, small, medium, large-v2, large-v3).
            device: Device for computation (cpu, cuda, auto).
            compute_type: Quantization type (int8, float16, float32).
        """
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        """Agent name."""
        return "whisper_raw"

    @property
    def description(self) -> str:
        """Agent description."""
        return f"Local Whisper ({self._model_size}) transcription without context"

    async def _ensure_model(self) -> None:
        """Lazy load the Whisper model."""
        if self._model is not None:
            return

        async with self._lock:
            if self._model is not None:
                return

            logger.info(f"Loading Whisper model: {self._model_size}...")
            from faster_whisper import WhisperModel

            loop = asyncio.get_running_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                ),
            )
            logger.info("Whisper model loaded successfully")

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs: Any,
    ) -> TranscriptResult:
        """Transcribe audio using local Whisper model.

        Args:
            audio_data: Raw audio bytes.
            language: Optional ISO language code.
            **kwargs: Additional options (beam_size, vad_filter, context).

        Returns:
            TranscriptResult: Transcription result with segments.
        """
        await self._ensure_model()

        # Write audio to temp file (faster-whisper requires file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            beam_size = kwargs.get("beam_size", int(os.getenv("WHISPER_BEAM_SIZE", "1")))
            vad_filter = kwargs.get("vad_filter", True)

            # Build initial prompt from context (vocabulary hints)
            initial_prompt = None
            if context := kwargs.get("context"):
                parts = []
                if vocab := context.get("vocabulary"):
                    if isinstance(vocab, list):
                        parts.append(", ".join(vocab))
                    else:
                        parts.append(str(vocab))
                if prompt := context.get("prompt"):
                    parts.append(prompt)
                if parts:
                    initial_prompt = " ".join(parts)
                    logger.info(f"Using initial_prompt: {initial_prompt[:100]}...")

            loop = asyncio.get_running_loop()
            segments_gen, info = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(
                    temp_path,
                    beam_size=beam_size,
                    language=language,
                    vad_filter=vad_filter,
                    vad_parameters=dict(min_silence_duration_ms=500),
                    initial_prompt=initial_prompt,
                ),
            )

            # Convert generator to list in executor
            raw_segments = await loop.run_in_executor(None, list, segments_gen)

            # Build TranscriptSegment list
            result_segments: list[TranscriptSegment] = []
            total_confidence = 0.0

            for seg in raw_segments:
                # faster-whisper provides avg_logprob, convert to confidence
                # logprob typically ranges from -1 to 0, we normalize
                confidence = min(1.0, max(0.0, 1.0 + seg.avg_logprob))
                total_confidence += confidence

                result_segments.append(
                    TranscriptSegment(
                        start=seg.start,
                        end=seg.end,
                        text=seg.text.strip(),
                        confidence=round(confidence, 3),
                        speaker=None,
                    )
                )

            avg_confidence = (
                total_confidence / len(result_segments) if result_segments else 0.0
            )

            return TranscriptResult(
                agent_name=self.name,
                language=info.language or "unknown",
                segments=result_segments,
                avg_confidence=round(avg_confidence, 3),
                meta={
                    "model_size": self._model_size,
                    "duration": info.duration,
                    "language_probability": info.language_probability,
                    "device": self._device,
                },
            )

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def health_check(self) -> bool:
        """Check if model can be loaded."""
        try:
            await self._ensure_model()
            return self._model is not None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Factory function for easy instantiation
def create_agent(
    model_size: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
) -> WhisperRawAgent:
    """Create a WhisperRawAgent with environment defaults.

    Args:
        model_size: Model size override.
        device: Device override.
        compute_type: Compute type override.

    Returns:
        WhisperRawAgent: Configured agent instance.
    """
    return WhisperRawAgent(
        model_size=model_size or os.getenv("WHISPER_MODEL_SIZE", "small"),
        device=device or os.getenv("WHISPER_DEVICE", "auto"),
        compute_type=compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
    )
