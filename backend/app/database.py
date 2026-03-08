"""Database configuration — SQLAlchemy + Supabase (PostgreSQL)."""

import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import get_settings

logger = logging.getLogger("transcribeai.database")
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

# Supabase connection pooler: use port 6543 for IPv4 pooled connections
# Direct connection (port 5432) uses IPv6 which many hosts don't support
if "supabase.co" in DATABASE_URL and ":5432/" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace(":5432/", ":6543/")
    logger.info("Switched to Supabase connection pooler (port 6543)")

# Handle SQLite vs PostgreSQL specific settings
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args = {"connect_args": {"check_same_thread": False}}
else:
    # Postgres pooling / keepalive for Supabase
    engine_args = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "connect_timeout": 10,
        },
    }

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Graceful on connection failure."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified")
    except Exception as e:
        logger.warning("Database init failed (will retry on first request): %s", e)
