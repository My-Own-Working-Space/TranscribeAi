"""Authentication endpoints — Supabase integration."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.services.auth_service import decode_token, get_user_by_id

router = APIRouter()
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: extract and validate Supabase JWT → return local User profile."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # 1. Verify token via Supabase
    user_id = decode_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # 2. Get local profile (sync if missing)
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Profile not found")
    
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
