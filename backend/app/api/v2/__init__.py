from fastapi import APIRouter
from app.api.v2.endpoints import auth, jobs, ai, feedback

v2_router = APIRouter()
v2_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v2_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
v2_router.include_router(ai.router, prefix="/jobs", tags=["ai-features"])
v2_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
