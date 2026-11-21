"""
api/database.py — SQLAlchemy engine + session dependency
"""

import os
import re

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

_raw_url = (os.getenv("DATABASE_URL") or "").strip().strip('"').strip("'")
# channel_binding=require can break some serverless Postgres drivers
DATABASE_URL = re.sub(r"[&?]channel_binding=require", "", _raw_url)

engine = None
SessionLocal = None

if DATABASE_URL:
    # NullPool is correct for serverless — no persistent connection pool
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
        connect_args={"connect_timeout": 10},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that provides a DB session and ensures it is closed."""
    if SessionLocal is None or engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured. Set DATABASE_URL on Vercel and redeploy.",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
