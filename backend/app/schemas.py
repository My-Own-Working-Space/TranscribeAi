"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, BeforeValidator
from typing import Annotated, Optional
from datetime import datetime

# Supabase/Postgres returns native UUID objects; coerce to str for JSON responses.
StrUUID = Annotated[str, BeforeValidator(lambda v: str(v) if not isinstance(v, str) else v)]


class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: StrUUID
    email: str
    full_name: str
    plan: str
    monthly_minutes_used: int
    monthly_minutes_limit: int
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SegmentData(BaseModel):
    """Segment stored as JSON element inside TranscriptionJob.segments_json."""
    index: int = 0
    start: float = 0.0
    end: float = 0.0
    text: str = ""
    confidence: float = 0.0
    speaker: Optional[str] = None


class SummaryResponse(BaseModel):
    id: StrUUID
    summary: Optional[str] = None
    key_points: Optional[list] = []
    conclusion: Optional[str] = None
    llm_model: Optional[str] = None
    review_passes: Optional[int] = 0
    generated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActionItemResponse(BaseModel):
    id: StrUUID
    task_description: str
    assignee: str
    deadline: str
    priority: str
    is_completed: bool

    class Config:
        from_attributes = True


class ActionItemUpdate(BaseModel):
    is_completed: Optional[bool] = None
    priority: Optional[str] = None


class JobListResponse(BaseModel):
    id: StrUUID
    status: str
    original_filename: Optional[str] = None
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    overall_confidence: float = 0.0
    processing_time_s: float = 0.0
    mode: str = "standard"
    language_detected: Optional[str] = None
    has_summary: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobDetailResponse(BaseModel):
    id: StrUUID
    status: str
    original_filename: Optional[str] = None
    file_size_bytes: int = 0
    duration_seconds: float = 0.0
    overall_confidence: float = 0.0
    processing_time_s: float = 0.0
    whisper_model: str = ""
    mode: str = "standard"
    language_detected: Optional[str] = None
    transcript: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    segments: list[SegmentData] = []
    summary: Optional[SummaryResponse] = None
    action_items: list[ActionItemResponse] = []

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []


class DashboardStats(BaseModel):
    total_jobs: int
    completed_jobs: int
    total_minutes_transcribed: float
    minutes_used_this_month: int
    minutes_limit: int
    plan: str


class FeedbackCreate(BaseModel):
    name: str = ""
    email: str = ""
    feedback_type: str = "general"
    message: str
