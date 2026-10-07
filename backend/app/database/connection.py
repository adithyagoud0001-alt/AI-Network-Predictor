"""Database Connection and Session Management Module

Supports PostgreSQL (production) with automatic SQLite fallback for immediate local runs.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

db_url = settings.DATABASE_URL

# Normalize sqlite path if relative
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True
    )
    # Test connection
    with engine.connect() as conn:
        logger.info(f"Connected to database successfully ({db_url.split('@')[-1]})")
except Exception as exc:
    logger.warning(f"Failed to connect to primary DB ({db_url}): {exc}. Falling back to SQLite.")
    sqlite_url = "sqlite:///./network_predictor.db"
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
