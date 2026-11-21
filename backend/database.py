from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.database import Base
from db.database import get_db
from db.database import get_engine
from db.database import get_session_factory


REQUIRED_TABLES = {
    "hospital_admin",
    "hospital_subscription",
    "learning_media",
    "patients",
    "patient_sessions",
    "quiz_attempts",
    "quiz_answers",
    "patient_reports",
}


def initialize_database() -> bool:
    engine = get_engine()
    if engine is None:
        return False

    try:
        with engine.connect() as connection:
            table_rows = connection.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
            ).fetchall()
            session_column_rows = connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'patient_sessions'
                    """
                )
            ).fetchall()
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "Could not connect to Supabase PostgreSQL. Check DATABASE_URL, network access, and SSL settings."
        ) from exc

    available_tables = {row[0] for row in table_rows}
    missing_tables = sorted(REQUIRED_TABLES - available_tables)
    if missing_tables:
        raise RuntimeError(
            "Supabase schema is missing required tables: " + ", ".join(missing_tables)
        )
    session_columns = {row[0] for row in session_column_rows}
    if "draft_profile" not in session_columns:
        raise RuntimeError(
            "Supabase schema is missing patient_sessions.draft_profile. "
            "Run backend/migrations/2026_11_20_add_patient_session_draft_profile.sql before deploying."
        )
    return True


@contextmanager
def db_session_scope() -> Iterator[Session]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
