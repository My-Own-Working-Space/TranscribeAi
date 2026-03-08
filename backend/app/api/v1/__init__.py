from fastapi import APIRouter, Depends
from app.api.v1.endpoints import transcribe, export, tts
from app.api.v2.endpoints.auth import get_current_user

api_router = APIRouter(dependencies=[Depends(get_current_user)])
api_router.include_router(transcribe.router, prefix="/transcribe", tags=["transcribe"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(tts.router, prefix="/tts", tags=["tts"])
