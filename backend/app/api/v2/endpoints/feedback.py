"""Feedback endpoint — anyone can submit feedback (auth optional)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Feedback
from app.schemas import FeedbackCreate

router = APIRouter()


@router.post("/", status_code=201)
async def submit_feedback(body: FeedbackCreate, db: Session = Depends(get_db)):
    """Accept user feedback. No auth required."""
    if not body.message.strip():
        raise HTTPException(400, "Message is required")

    fb = Feedback(
        name=body.name.strip()[:255],
        email=body.email.strip()[:255],
        feedback_type=body.feedback_type if body.feedback_type in ("general", "bug", "feature", "other") else "general",
        message=body.message.strip()[:5000],
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "message": "Feedback received. Thank you!"}
