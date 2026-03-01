"""Post-processing service for transcription correction.

Uses LLM to fix transcription errors without needing vocabulary hints.
"""

import logging
import os
from typing import Any

import httpx

from app.config import settings
from app.schemas import FinalTranscript, TranscriptSegment

logger = logging.getLogger(__name__)

# Common technical terms that are often mistranscribed
TECH_CORRECTIONS = {
    "AFB.NET": "ASP.NET",
    "AFB .NET": "ASP.NET",
    "asp.net": "ASP.NET",
    "a.s.p.net": "ASP.NET",
    "Entity framework": "Entity Framework",
    "entity framework": "Entity Framework",
    "Visual studio": "Visual Studio",
    "visual studio": "Visual Studio",
    "c sharp": "C#",
    "C sharp": "C#",
    "sea sharp": "C#",
    "dot net": ".NET",
    "dotnet": ".NET",
    ".net core": ".NET Core",
    "react js": "React.js",
    "React JS": "React.js",
    "node js": "Node.js",
    "Node JS": "Node.js",
    "vue js": "Vue.js",
    "Vue JS": "Vue.js",
    "next js": "Next.js",
    "Next JS": "Next.js",
    "type script": "TypeScript",
    "java script": "JavaScript",
    "Java script": "JavaScript",
    "my sql": "MySQL",
    "My SQL": "MySQL",
    "mongo db": "MongoDB",
    "Mongo DB": "MongoDB",
    "post gres": "PostgreSQL",
    "postgres": "PostgreSQL",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "AWS": "AWS",
    "azure": "Azure",
    "git hub": "GitHub",
    "Git Hub": "GitHub",
    "git lab": "GitLab",
    "Git Lab": "GitLab",
    "API": "API",
    "a p i": "API",
    "rest api": "REST API",
    "Rest API": "REST API",
    "graphql": "GraphQL",
    "Graph QL": "GraphQL",
    "http": "HTTP",
    "https": "HTTPS",
    "json": "JSON",
    "xml": "XML",
    "html": "HTML",
    "css": "CSS",
    "sql": "SQL",
}


class TranscriptPostProcessor:
    """Post-processor for fixing transcription errors."""

    def __init__(
        self,
        use_llm: bool = True,
        llm_provider: str = "groq",
    ) -> None:
        """Initialize the post-processor.

        Args:
            use_llm: Whether to use LLM for advanced corrections.
            llm_provider: LLM provider (groq, openai).
        """
        self._use_llm = use_llm
        self._provider = llm_provider
        self._api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    def _apply_basic_corrections(self, text: str) -> str:
        """Apply rule-based corrections for common mistakes.

        Args:
            text: Original transcription text.

        Returns:
            str: Corrected text.
        """
        result = text
        for wrong, correct in TECH_CORRECTIONS.items():
            # Case-sensitive replacement
            result = result.replace(wrong, correct)
        return result

    async def _correct_with_llm(self, text: str, language: str = "vi") -> str:
        """Use LLM to correct transcription errors.

        Args:
            text: Original transcription text.
            language: Language code.

        Returns:
            str: LLM-corrected text.
        """
        if not self._api_key:
            logger.warning("No API key for LLM, skipping LLM correction")
            return text

        client = await self._ensure_client()

        system_prompt = """You are a transcription correction assistant. 
Fix technical terms and proper nouns that were likely mistranscribed by speech-to-text.

Common errors to fix:
- "AFB.NET" or "AFB .NET" → "ASP.NET"
- "c sharp" or "sea sharp" → "C#"
- "dot net" → ".NET"
- Technology names should use proper casing

Rules:
1. Only fix obvious transcription errors
2. Don't change the meaning or structure
3. Keep the same language
4. Return ONLY the corrected text, no explanations"""

        user_prompt = f"Fix transcription errors in this text:\n\n{text}"

        try:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": len(text) + 500,
                },
            )

            response.raise_for_status()
            data = response.json()
            corrected = data["choices"][0]["message"]["content"].strip()
            
            logger.info(f"LLM correction applied: {len(text)} → {len(corrected)} chars")
            return corrected

        except Exception as e:
            logger.error(f"LLM correction failed: {e}")
            return text

    async def process_segment(
        self,
        segment: TranscriptSegment,
        use_llm: bool = False,
    ) -> TranscriptSegment:
        """Process a single segment.

        Args:
            segment: Original segment.
            use_llm: Whether to use LLM for this segment.

        Returns:
            TranscriptSegment: Corrected segment.
        """
        corrected_text = self._apply_basic_corrections(segment.text)

        if use_llm and self._use_llm and corrected_text != segment.text:
            # Only use LLM if basic correction made changes (likely has errors)
            corrected_text = await self._correct_with_llm(corrected_text)

        return TranscriptSegment(
            start=segment.start,
            end=segment.end,
            text=corrected_text,
            confidence=segment.confidence,
            speaker=segment.speaker,
        )

    async def process_transcript(
        self,
        transcript: FinalTranscript,
        use_llm: bool = True,
    ) -> FinalTranscript:
        """Process entire transcript with corrections.

        Args:
            transcript: Original transcript.
            use_llm: Whether to use LLM for advanced corrections.

        Returns:
            FinalTranscript: Corrected transcript.
        """
        # First, apply basic corrections to all segments
        corrected_segments = []
        for seg in transcript.segments:
            corrected = await self.process_segment(seg, use_llm=False)
            corrected_segments.append(corrected)

        # If LLM is enabled, process the full text for context-aware correction
        if use_llm and self._use_llm:
            full_text = " ".join(s.text for s in corrected_segments)
            corrected_full = await self._correct_with_llm(full_text)

            # Update notes with correction info
            notes = transcript.notes or ""
            if corrected_full != full_text:
                notes += " | Post-processed with LLM"

            return FinalTranscript(
                segments=corrected_segments,
                overall_confidence=transcript.overall_confidence,
                notes=notes,
                full_text=corrected_full,
            )

        return FinalTranscript(
            segments=corrected_segments,
            overall_confidence=transcript.overall_confidence,
            notes=transcript.notes,
        )

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()


# Singleton instance
_post_processor: TranscriptPostProcessor | None = None


def get_post_processor() -> TranscriptPostProcessor:
    """Get or create the post-processor singleton."""
    global _post_processor
    if _post_processor is None:
        _post_processor = TranscriptPostProcessor()
    return _post_processor
