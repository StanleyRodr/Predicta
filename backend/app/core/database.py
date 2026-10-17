"""Database engine and session factory.

SQLAlchemy 2.0 setup with PostgreSQL. The connection string is read
from the ``DATABASE_URL`` environment variable. Schema is managed via
Alembic (see ``alembic/``); ``Base.metadata.create_all`` is intentionally
not called at runtime.
"""

from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

import os

SQLALCHEMY_DATABASE_URL: str = os.environ["DATABASE_URL"]

# pool_pre_ping=True drops dead connections automatically, important
# for long-running services and after DB restarts.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session.

    Ensures the session is closed after the request completes, even
    when an exception is raised inside the handler.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
