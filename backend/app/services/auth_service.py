"""Authentication service — Supabase JWT verification."""

import logging
from typing import Optional

import jwt as pyjwt
from supabase import create_client, Client
from app.config import get_settings
from app.models import User
from sqlalchemy.orm import Session

logger = logging.getLogger("transcribeai.auth")
settings = get_settings()
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def _decode_jwt_local(token: str) -> Optional[str]:
    """Verify JWT locally using SUPABASE_JWT_SECRET (fast, no network call)."""
    try:
        payload = pyjwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload.get("sub")  # Supabase user id
    except pyjwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except pyjwt.InvalidTokenError as e:
        logger.debug("JWT invalid: %s", e)
        return None


def _decode_jwt_remote(token: str) -> Optional[str]:
    """Verify JWT via Supabase Auth API (slow fallback, requires network)."""
    try:
        res = supabase.auth.get_user(token)
        if res and res.user:
            return str(res.user.id)
        return None
    except Exception:
        return None


def decode_token(token: str) -> Optional[str]:
    """Verify Supabase JWT — local first, remote fallback."""
    if settings.SUPABASE_JWT_SECRET:
        uid = _decode_jwt_local(token)
        if uid:
            return uid
        # Local failed → try remote (token might use different algorithm)
        logger.debug("Local JWT decode failed, trying remote verification")

    return _decode_jwt_remote(token)


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get or sync user profile from DB."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Fallback profile sync if DB trigger missed something
        try:
            res = supabase.from_("profiles").select("*").eq("id", user_id).execute()
            if res.data:
                data = res.data[0]
                user = User(
                    id=data["id"],
                    email=data["email"],
                    full_name=data.get("full_name", ""),
                    plan=data.get("plan", "free")
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        except Exception:
            return None
    return user
