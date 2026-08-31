from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

if is_sqlite:
    # SQLite does NOT enforce foreign keys (including our ON DELETE CASCADE
    # constraints — see DATABASE_SCHEMA.md) unless this pragma is set on
    # every connection. Without it, cascade delete only appears to work when
    # going through SQLAlchemy's ORM-level `cascade="all, delete-orphan"`
    # (session.delete(obj)) — any bulk `.delete()` query or raw SQL DELETE
    # would silently leave orphaned child rows.
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
