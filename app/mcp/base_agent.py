"""Base interface for transcription agents.

All transcription agents must implement this interface for orchestrator compatibility.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas import TranscriptResult


class BaseTranscriptionAgent(ABC):
    """Abstract base class for transcription agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent name for identification."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of the agent."""
        return f"{self.name} transcription agent"

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs: Any,
    ) -> TranscriptResult:
        """Transcribe audio data.

        Args:
            audio_data: Raw audio bytes.
            language: Optional ISO language code. None for auto-detect.
            **kwargs: Agent-specific options.

        Returns:
            TranscriptResult: Transcription result with segments.
        """
        ...

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests.

        Returns:
            bool: True if healthy, False otherwise.
        """
        return True

    def get_tool_schema(self) -> dict[str, Any]:
        """Return MCP tool schema for this agent.

        Returns:
            dict: Tool schema following MCP specification.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "audio_path": {"type": "string", "description": "Path to audio file"},
                    "language": {"type": "string", "description": "ISO language code"},
                },
                "required": ["audio_path"],
            },
        }
