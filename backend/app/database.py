"""Database configuration — SQLAlchemy + Supabase (PostgreSQL)."""

import logging
import re
import socket
from urllib.parse import urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import get_settings

logger = logging.getLogger("transcribeai.database")
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL


def _rewrite_to_pooler(url: str) -> str:
    """
    Supabase 'db.xxx.supabase.co' resolves to IPv6 ONLY.
    Render (and many hosts) don't support IPv6 outbound.
    Fix: rewrite to Supavisor pooler hostname (IPv4).

    Direct:  postgresql://postgres:[pw]@db.PROJECT.supabase.co:5432/postgres
    Pooler:  postgresql://postgres.PROJECT:[pw]@aws-N-REGION.pooler.supabase.com:6543/postgres
    """
    if "supabase.co" not in url:
        return url

    parsed = urlparse(url)
    host = parsed.hostname or ""

    # Already using pooler — nothing to do
    if "pooler.supabase.com" in host:
        logger.info("Already using Supabase pooler: %s", host)
        return url

    # Extract project ref from 'db.PROJECT.supabase.co'
    match = re.match(r"db\.([a-z0-9]+)\.supabase\.co", host)
    if not match:
        return url

    project_ref = match.group(1)
    password = parsed.password or ""
    dbname = parsed.path.lstrip("/") or "postgres"

    # Try pooler hostnames: aws-0, aws-1, aws-2 × common regions
    # Each Supabase project is registered on one specific prefix — must verify
    regions = ["ap-southeast-1", "us-east-1", "eu-west-1", "us-west-1",
               "ap-northeast-1", "eu-central-1"]
    prefixes = ["aws-1", "aws-0", "aws-2"]  # aws-1 first (newer projects)

    for prefix in prefixes:
        for region in regions:
            pooler_host = f"{prefix}-{region}.pooler.supabase.com"
            try:
                # Check if this hostname resolves to IPv4
                results = socket.getaddrinfo(pooler_host, 6543, socket.AF_INET, socket.SOCK_STREAM)
                if results:
                    ipv4 = results[0][4][0]
                    new_url = (
                        f"postgresql://postgres.{project_ref}:{password}"
                        f"@{pooler_host}:6543/{dbname}"
                    )
                    logger.info(
                        "Rewrote Supabase URL → %s (%s, IPv4)",
                        pooler_host, ipv4,
                    )
                    return new_url
            except socket.gaierror:
                continue

    logger.warning("No IPv4 pooler found for project %s — keeping original URL", project_ref)
    return url


DATABASE_URL = _rewrite_to_pooler(DATABASE_URL)

# Handle SQLite vs PostgreSQL specific settings
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args = {"connect_args": {"check_same_thread": False}}
else:
    engine_args = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"connect_timeout": 10},
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
