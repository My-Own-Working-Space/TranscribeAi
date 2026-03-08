"""SQLAlchemy ORM models for TranscribeAI — Supabase (Postgres) version."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class User(Base):
    """Maps to 'profiles' table in Supabase."""
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True)  # UUID from Supabase Auth
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), default="")
    plan = Column(String(20), default="free")
    monthly_minutes_used = Column(Integer, default=0)
    monthly_minutes_limit = Column(Integer, default=9999)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    jobs = relationship("TranscriptionJob", back_populates="user", cascade="all, delete-orphan")


class TranscriptionJob(Base):
    __tablename__ = "transcription_jobs"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="queued")
    original_filename = Column(String(500))
    storage_path = Column(String(1000))
    file_size_bytes = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    whisper_model = Column(String(50), default="base")
    language_detected = Column(String(10))
    overall_confidence = Column(Float, default=0.0)
    processing_time_s = Column(Float, default=0.0)
    transcript = Column(Text, default="")
    segments_json = Column(JSON, default=list)  # [{index, start, end, text, confidence, speaker}]
    mode = Column(String(20), default="standard")
    error = Column(Text)
    created_at = Column(DateTime, default=_now)
    completed_at = Column(DateTime)

    user = relationship("User", back_populates="jobs")
    summary = relationship("AISummary", back_populates="job", uselist=False, cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_jobs_user_status", "user_id", "status"),
        Index("idx_jobs_created_at_desc", "created_at"),
    )


class TranscriptSegment(Base):
    """DEPRECATED — kept for migration compatibility. New data goes to TranscriptionJob.segments_json."""
    __tablename__ = "transcript_segments"

    id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("transcription_jobs.id", ondelete="CASCADE"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    speaker_label = Column(String(50))


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("transcription_jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary = Column(Text)
    key_points = Column(JSON)
    conclusion = Column(Text)
    llm_model = Column(String(100))
    review_passes = Column(Integer, default=0)
    generated_at = Column(DateTime, default=_now)

    job = relationship("TranscriptionJob", back_populates="summary")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    job_id = Column(String(36), ForeignKey("transcription_jobs.id", ondelete="CASCADE"), nullable=False)
    task_description = Column(Text, nullable=False)
    assignee = Column(String(255), default="Unassigned")
    deadline = Column(String(255), default="Not specified")
    priority = Column(String(10), default="medium")
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_now)

    job = relationship("TranscriptionJob", back_populates="action_items")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), nullable=True)  # optional, no FK — works for anonymous users too
    name = Column(String(255), default="")
    email = Column(String(255), default="")
    feedback_type = Column(String(20), default="general")   # general | bug | feature | other
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)


# ChatMessage removed — chat history now stored in Redis sessions.
