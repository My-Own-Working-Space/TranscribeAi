"""Transcript data schemas for multi-agent speech-to-text system."""

from typing import Optional

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    """A single segment of transcribed speech."""

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    speaker: Optional[str] = Field(default=None, description="Speaker identifier")


class TranscriptResult(BaseModel):
    """Result from a single transcription agent."""

    agent_name: str = Field(..., description="Name of the transcription agent")
    language: str = Field(..., description="Detected or specified language code")
    segments: list[TranscriptSegment] = Field(default_factory=list, description="List of transcript segments")
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    meta: dict = Field(default_factory=dict, description="Additional metadata")


class FinalTranscript(BaseModel):
    """Final merged transcript from all agents."""

    segments: list[TranscriptSegment] = Field(default_factory=list, description="Merged transcript segments")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    notes: Optional[str] = Field(default=None, description="Additional notes or comments")
    full_text: Optional[str] = Field(default=None, description="Full corrected text (after post-processing)")
