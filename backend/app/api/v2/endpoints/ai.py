"""AI feature endpoints — summary, chat, action items."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TranscriptionJob, ActionItem, User
from app.schemas import (
    SummaryResponse, ChatRequest, ChatResponse, ChatHistoryItem,
    ActionItemResponse, ActionItemUpdate,
)
from app.api.v2.endpoints.auth import get_current_user
from app.services.summary_service import summary_service
from app.services.chat_service import chat_service
from app.services.action_service import action_service

router = APIRouter()


def _get_user_job(job_id: str, user: User, db: Session) -> TranscriptionJob:
    job = db.query(TranscriptionJob).filter(
        TranscriptionJob.id == job_id, TranscriptionJob.user_id == user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")
    return job


@router.get("/{job_id}/summary", response_model=SummaryResponse)
def get_summary(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_user_job(job_id, current_user, db)
    if not job.summary:
        raise HTTPException(status_code=404, detail="No summary generated yet")
    return SummaryResponse.model_validate(job.summary)


@router.post("/{job_id}/summary/regenerate", response_model=SummaryResponse)
def regenerate_summary(
    job_id: str,
    language: str = Query(None, description="Target language: vi or en"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_user_job(job_id, current_user, db)
    try:
        s = summary_service.generate_summary(db, job, language=language)
        return SummaryResponse.model_validate(s)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e}")


@router.post("/{job_id}/chat", response_model=ChatResponse)
def chat_with_transcript(
    job_id: str, data: ChatRequest,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    job = _get_user_job(job_id, current_user, db)
    try:
        result = chat_service.answer_question(db, job, current_user.id, data.message)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")


@router.get("/{job_id}/chat/history", response_model=list[ChatHistoryItem])
def get_chat_history(
    job_id: str,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _get_user_job(job_id, current_user, db)
    msgs = chat_service.get_history(job_id, current_user.id)
    return msgs


@router.delete("/{job_id}/chat/history", status_code=204)
def clear_chat_history(
    job_id: str,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Clear chat session for this job (Redis)."""
    _get_user_job(job_id, current_user, db)
    chat_service.clear_history(job_id, current_user.id)


@router.get("/{job_id}/actions", response_model=list[ActionItemResponse])
def get_actions(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_user_job(job_id, current_user, db)
    return [ActionItemResponse.model_validate(a) for a in job.action_items]


@router.post("/{job_id}/actions/extract", response_model=list[ActionItemResponse])
def extract_actions(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_user_job(job_id, current_user, db)
    try:
        items = action_service.extract_actions(db, job)
        return [ActionItemResponse.model_validate(a) for a in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")


@router.patch("/{job_id}/actions/{action_id}", response_model=ActionItemResponse)
def update_action(
    job_id: str, action_id: str, data: ActionItemUpdate,
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    _get_user_job(job_id, current_user, db)
    item = db.query(ActionItem).filter(ActionItem.id == action_id, ActionItem.job_id == job_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    if data.is_completed is not None:
        item.is_completed = data.is_completed
    if data.priority is not None:
        item.priority = data.priority
    db.commit()
    db.refresh(item)
    return ActionItemResponse.model_validate(item)
