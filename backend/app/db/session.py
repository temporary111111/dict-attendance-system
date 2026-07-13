"""Database engine at session helpers.

Ito ang shared entry point ng app kapag kailangan makipag-usap sa MySQL.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def create_database_engine(database_url: str) -> Engine:
    """Gumagawa ng SQLAlchemy engine gamit ang database URL from settings."""
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


settings = get_settings()
engine = create_database_engine(settings.database_url)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Isang DB session per request; automatic sinasara pagkatapos gamitin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
