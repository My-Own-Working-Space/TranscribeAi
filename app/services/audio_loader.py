"""Audio loading and preprocessing service.

This module handles audio file loading, format validation, and preprocessing
for transcription agents.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import BinaryIO

import aiofiles

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_FORMATS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
    ".mp4",
    ".mkv",
    ".webm",
    ".aac",
}


class AudioLoader:
    """Service for loading and preprocessing audio files."""

    def __init__(self, max_size_mb: int = 100) -> None:
        """Initialize the audio loader.

        Args:
            max_size_mb: Maximum allowed file size in MB.
        """
        self._max_size_bytes = max_size_mb * 1024 * 1024

    def _validate_format(self, path: Path) -> bool:
        """Check if file format is supported.

        Args:
            path: Path to validate.

        Returns:
            bool: True if format is supported.
        """
        return path.suffix.lower() in SUPPORTED_FORMATS

    def _validate_size(self, path: Path) -> bool:
        """Check if file size is within limits.

        Args:
            path: Path to validate.

        Returns:
            bool: True if size is acceptable.
        """
        return path.stat().st_size <= self._max_size_bytes

    async def load_file(self, path: str | Path) -> bytes:
        """Load audio file from disk.

        Args:
            path: Path to the audio file.

        Returns:
            bytes: Raw audio data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If format unsupported or file too large.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        if not self._validate_format(path):
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {', '.join(SUPPORTED_FORMATS)}"
            )

        if not self._validate_size(path):
            size_mb = path.stat().st_size / (1024 * 1024)
            raise ValueError(
                f"File too large: {size_mb:.1f}MB. "
                f"Maximum: {self._max_size_bytes / (1024 * 1024):.0f}MB"
            )

        logger.info(f"Loading audio: {path} ({path.stat().st_size / 1024:.1f}KB)")

        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def load_stream(self, stream: BinaryIO, filename: str = "") -> bytes:
        """Load audio from a stream.

        Args:
            stream: Binary stream containing audio data.
            filename: Original filename for format detection.

        Returns:
            bytes: Raw audio data.

        Raises:
            ValueError: If format unsupported or stream too large.
        """
        # Check format from filename if provided
        if filename:
            path = Path(filename)
            if not self._validate_format(path):
                raise ValueError(f"Unsupported format: {path.suffix}")

        # Read stream
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, stream.read)

        if len(data) > self._max_size_bytes:
            size_mb = len(data) / (1024 * 1024)
            raise ValueError(
                f"Stream too large: {size_mb:.1f}MB. "
                f"Maximum: {self._max_size_bytes / (1024 * 1024):.0f}MB"
            )

        logger.info(f"Loaded audio stream: {len(data) / 1024:.1f}KB")
        return data

    async def get_metadata(self, path: str | Path) -> dict:
        """Extract metadata from audio file.

        Args:
            path: Path to the audio file.

        Returns:
            dict: Audio metadata (size, format, etc.)
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        stat = path.stat()
        return {
            "filename": path.name,
            "format": path.suffix.lower().lstrip("."),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "supported": self._validate_format(path),
            "within_size_limit": self._validate_size(path),
        }


# Global instance
_audio_loader: AudioLoader | None = None


def get_audio_loader() -> AudioLoader:
    """Get or create the global audio loader."""
    global _audio_loader
    if _audio_loader is None:
        max_size = int(os.getenv("MAX_AUDIO_SIZE_MB", "100"))
        _audio_loader = AudioLoader(max_size_mb=max_size)
    return _audio_loader
