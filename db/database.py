"""database"""

from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from config import settings
from db.models import Base

engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # reconnect on stale connections
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    logger.info("Initialising database schema...")
    Base.metadata.create_all(bind=engine)
    logger.success("Database schema ready.")


def check_connection() -> bool:
    """Return True if the DB is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"Database connection failed: {exc}")
        return False


@contextmanager
def get_db() -> Session:
    """Context-manager that yields a session and handles commit/rollback."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# FastAPI dependency (used in api/routes)
def get_db_dependency():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
