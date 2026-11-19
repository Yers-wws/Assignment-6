"""Database engine, session management, and Base model for Voltix TechStore.

Configured exclusively via DATABASE_URL environment variable.
"""

import os
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Load environment variables from .env in backend/ or root
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")
load_dotenv()


def get_database_url() -> str:
    """Retrieve and normalize database connection URL from environment."""
    url = os.getenv("DATABASE_URL")
    if not url:
        # Fallback to local sqlite database in backend directory
        db_path = BACKEND_DIR / "voltix.db"
        url = f"sqlite:///{db_path.as_posix()}"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = get_database_url()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy session and closing it on completion."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
