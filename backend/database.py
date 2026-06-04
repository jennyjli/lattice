"""
Database engine, session factory, and helpers.

Usage in FastAPI endpoints:
    from database import get_db
    from sqlalchemy.orm import Session

    @app.post("/...")
    def my_route(db: Session = Depends(get_db)):
        ...
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import DATABASE_URL
from models import Base

# SQLite needs pragma foreign_keys to enforce FKs
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    # SQLite: allow sharing a single connection across threads (needed for FastAPI dev)
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    echo=False,
)

if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(conn, _rec):
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create all tables if they don't exist (dev convenience)."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
