"""Context-aware transcription agent using Whisper with prompts.

This agent uses Whisper's prompt feature to inject vocabulary hints
and improve accuracy for domain-specific content.
"""

import asyncio
import logging
import os
import tempfile
from typing import Any

from app.mcp.base_agent import BaseTranscriptionAgent
from app.schemas import TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class WhisperContextAgent(BaseTranscriptionAgent):
    """Context-aware Whisper transcription using prompts and vocabulary."""

    def __init__(
        self,
        model_size: str = "medium",
        device: str = "auto",
        compute_type: str = "int8",
    ) -> None:
        """Initialize the context-aware Whisper agent.

        Args:
            model_size: Model size (recommend medium+ for context).
            device: Device for computation.
            compute_type: Quantization type.
        """
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None
        self._lock = asyncio.Lock()

    @property
    def name(self) -> str:
        """Agent name."""
        return "whisper_context"

    @property
    def description(self) -> str:
        """Agent description."""
        return f"Context-aware Whisper ({self._model_size}) with vocabulary hints"

    async def _ensure_model(self) -> None:
        """Lazy load the Whisper model."""
        if self._model is not None:
            return

        async with self._lock:
            if self._model is not None:
                return

            logger.info(f"Loading Whisper context model: {self._model_size}...")
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
            logger.info("Whisper context model loaded")

    def _build_prompt(self, context: dict[str, Any] | None) -> str | None:
        """Build a prompt from context dictionary.

        Args:
            context: Context with vocabulary, domain, etc.

        Returns:
            str | None: Prompt string or None.
        """
        if not context:
            return None

        parts: list[str] = []

        # Add vocabulary terms
        if vocab := context.get("vocabulary"):
            if isinstance(vocab, list):
                parts.append(", ".join(vocab))
            elif isinstance(vocab, str):
                parts.append(vocab)

        # Add domain context
        if domain := context.get("domain"):
            parts.append(f"This is about {domain}.")

        # Add custom prompt
        if custom := context.get("prompt"):
            parts.append(custom)

        return " ".join(parts) if parts else None

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs: Any,
    ) -> TranscriptResult:
        """Transcribe audio with context enhancement.

        Args:
            audio_data: Raw audio bytes.
            language: Optional ISO language code.
            **kwargs: Must include 'context' dict with vocabulary/domain hints.

        Returns:
            TranscriptResult: Context-enhanced transcription result.
        """
        await self._ensure_model()

        context = kwargs.get("context", {})
        initial_prompt = self._build_prompt(context)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        try:
            loop = asyncio.get_running_loop()
            segments_gen, info = await loop.run_in_executor(
                None,
                lambda: self._model.transcribe(
                    temp_path,
                    beam_size=5,  # Higher beam for better accuracy
                    language=language,
                    vad_filter=True,
                    initial_prompt=initial_prompt,
                    condition_on_previous_text=True,
                ),
            )

            raw_segments = await loop.run_in_executor(None, list, segments_gen)

            result_segments: list[TranscriptSegment] = []
            total_confidence = 0.0

            for seg in raw_segments:
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
                    "initial_prompt": initial_prompt,
                    "context_keys": list(context.keys()) if context else [],
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
            logger.error(f"Context agent health check failed: {e}")
            return False


def create_agent(
    model_size: str | None = None,
    device: str | None = None,
    compute_type: str | None = None,
) -> WhisperContextAgent:
    """Create a WhisperContextAgent with environment defaults."""
    return WhisperContextAgent(
        model_size=model_size or os.getenv("WHISPER_CONTEXT_MODEL_SIZE", "medium"),
        device=device or os.getenv("WHISPER_DEVICE", "auto"),
        compute_type=compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
    )
