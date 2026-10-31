"""
Database session management and connection diagnostics for Veritas.
"""

from typing import Any, Dict, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from backend.app.core.config import settings
from backend.app.core.logging import logger


def get_engine_args(url: str) -> Dict[str, Any]:
    args: Dict[str, Any] = {}
    if url.startswith("sqlite"):
        args["connect_args"] = {"check_same_thread": False}
    else:
        args["pool_pre_ping"] = True
    return args


engine = create_engine(
    settings.DATABASE_URL,
    **get_engine_args(settings.DATABASE_URL),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields an active database session, rolling back on error."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_health() -> Dict[str, Any]:
    """
    Actually tests database responsiveness using a lightweight probe.
    Does not falsely claim connectivity.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            if result == 1:
                return {
                    "status": "healthy",
                    "dialect": engine.dialect.name,
                    "connected": True,
                }
            return {
                "status": "unhealthy",
                "detail": "Probe query did not return expected scalar value.",
                "connected": False,
            }
    except Exception as exc:
        logger.warning(f"Database health probe failed: {exc}")
        return {
            "status": "unhealthy",
            "detail": str(exc),
            "connected": False,
        }

