"""MCP tools for transcription operations.

Available tools:
- transcribe_raw: Local Whisper transcription
- transcribe_context: Context-aware transcription with vocabulary hints
- transcribe_external: External API transcription (OpenAI, Groq)
- merge_transcript: Merge results from multiple agents
"""

from app.mcp.tools import (
    merge_transcript,
    transcribe_context,
    transcribe_external,
    transcribe_raw,
)

__all__ = [
    "transcribe_raw",
    "transcribe_context",
    "transcribe_external",
    "merge_transcript",
]
