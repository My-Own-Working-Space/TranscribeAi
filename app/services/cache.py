"""Transcription cache service.

Caches transcription results by audio content hash to avoid re-processing.
"""

import hashlib
import json
import logging
import time
from typing import Any

from app.schemas import FinalTranscript, TranscriptSegment

logger = logging.getLogger(__name__)


class TranscriptCache:
    """In-memory cache for transcription results."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600) -> None:
        """Initialize cache.

        Args:
            max_size: Maximum number of cached entries.
            ttl_seconds: Time-to-live for cache entries.
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    @staticmethod
    def hash_audio(audio_data: bytes, language: str | None = None) -> str:
        """Generate hash key for audio data.

        Args:
            audio_data: Raw audio bytes.
            language: Language code (affects transcription).

        Returns:
            str: SHA256 hash of audio + settings.
        """
        # Hash first 1MB + last 1MB + length for large files
        if len(audio_data) > 2_000_000:
            sample = audio_data[:1_000_000] + audio_data[-1_000_000:]
            content = sample + str(len(audio_data)).encode()
        else:
            content = audio_data

        key = hashlib.sha256(content).hexdigest()[:16]
        if language:
            key = f"{key}_{language}"
        return key

    def get(self, key: str) -> FinalTranscript | None:
        """Get cached transcript.

        Args:
            key: Cache key from hash_audio().

        Returns:
            FinalTranscript or None if not cached/expired.
        """
        entry = self._cache.get(key)
        if not entry:
            self._misses += 1
            return None

        # Check TTL
        if time.time() - entry["timestamp"] > self._ttl:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        logger.info(f"Cache hit for {key} (hits={self._hits}, misses={self._misses})")

        # Reconstruct FinalTranscript from cached data
        return FinalTranscript(**entry["data"])

    def set(self, key: str, transcript: FinalTranscript) -> None:
        """Cache a transcript result.

        Args:
            key: Cache key from hash_audio().
            transcript: Transcription result to cache.
        """
        # Evict oldest if full
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
            logger.debug(f"Cache evicted: {oldest_key}")

        self._cache[key] = {
            "timestamp": time.time(),
            "data": transcript.model_dump(),
        }
        logger.info(f"Cached transcript: {key}")

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            int: Number of entries cleared.
        """
        count = len(self._cache)
        self._cache.clear()
        return count

    @property
    def stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
        }


# Singleton instance
_cache: TranscriptCache | None = None


def get_cache() -> TranscriptCache:
    """Get or create cache singleton."""
    global _cache
    if _cache is None:
        _cache = TranscriptCache()
    return _cache
