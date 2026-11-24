from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from routes import report_routes
from services.report_service import ReportService


SESSION_ID = "00000000-0000-4000-8000-000000000101"


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self.rows = rows or []
        self.scalar_value = scalar

    def mappings(self):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None

    def scalar(self):
        return self.scalar_value


class FakeDeleteDatabase:
    def __init__(self, *, fail_on=None, has_patient=True, has_session=True, has_report=True):
        self.fail_on = fail_on
        self.has_patient = has_patient
        self.has_session = has_session
        self.has_report = has_report
        self.statements = []
        self.parameters = []
        self.rolled_back = False
        self.committed = False

    def execute(self, statement, params=None):
        sql = str(statement)
        normalized = " ".join(sql.lower().split())
        params = params or {}
        self.statements.append(sql)
        self.parameters.append(params)
        if self.fail_on and self.fail_on in sql:
            raise SQLAlchemyError("simulated foreign-key failure")
        if "SELECT to_regclass" in sql:
            return FakeResult(scalar=params["relation_name"])
        if normalized.startswith("select id from patients") and "for update" in normalized:
            return FakeResult([{"id": 22}] if self.has_patient else [])
        if normalized.startswith("select ps.id from patient_sessions ps") and "for update" in normalized:
            return FakeResult([{"id": SESSION_ID}] if self.has_session else [])
        if normalized.startswith("select id from patient_reports") and "for update" in normalized:
            return FakeResult([{"id": 31}] if self.has_report else [])
        return FakeResult()


@contextmanager
def fake_db_scope(db):
    try:
        yield db
        db.committed = True
    except Exception:
        db.rolled_back = True
        raise


def test_delete_patient_removes_dependencies_in_fk_safe_order():
    db = FakeDeleteDatabase()
    outcome = ReportService(db).delete_patient_data("PAT-22", admin_id=7)
    deletes = [statement for statement in db.statements if statement.lstrip().startswith("DELETE")]
    tables_in_order = [
        next(table for table in (
            "checkpoint_writes", "checkpoint_blobs", "checkpoints", "quiz_answers",
            "quiz_attempts", "patient_reports", "patient_sessions", "patients",
        ) if f"DELETE FROM public.{table}" in statement or f"DELETE FROM {table}" in statement)
        for statement in deletes
    ]

    assert tables_in_order == [
        "checkpoint_writes", "checkpoint_blobs", "checkpoints", "quiz_answers",
        "quiz_attempts", "patient_reports", "patient_sessions", "patients",
    ]
    assert outcome["patient_ids"] == [22]
    assert outcome["session_ids"] == [SESSION_ID]
    assert all(
        params.get("admin_id") == 7
        for sql, params in zip(db.statements, db.parameters)
        if "patient_code" in sql
    )


def test_delete_patient_does_not_find_or_delete_another_admins_patient():
    db = FakeDeleteDatabase(has_patient=False, has_session=False, has_report=False)
    with pytest.raises(ValueError, match="not found"):
        ReportService(db).delete_patient_data("PAT-OTHER", admin_id=7)

    assert not any(statement.lstrip().startswith("DELETE") for statement in db.statements)
    assert all(
        params.get("admin_id") == 7
        for params in db.parameters
        if "patient_code" in params
    )


def test_delete_endpoint_returns_not_found_for_non_owned_patient(monkeypatch):
    db = FakeDeleteDatabase(has_patient=False, has_session=False, has_report=False)
    monkeypatch.setattr(report_routes, "db_session_scope", lambda: fake_db_scope(db))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(audio_service=None)))

    with pytest.raises(HTTPException) as error:
        report_routes.delete_admin_patient("PAT-OTHER", request, SimpleNamespace(id=7))

    assert error.value.status_code == 404
    assert not any(statement.lstrip().startswith("DELETE") for statement in db.statements)


def test_delete_endpoint_rolls_back_and_returns_clear_failure(monkeypatch):
    db = FakeDeleteDatabase(fail_on="DELETE FROM quiz_attempts")
    monkeypatch.setattr(report_routes, "db_session_scope", lambda: fake_db_scope(db))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(audio_service=None)))

    with pytest.raises(HTTPException) as error:
        report_routes.delete_admin_patient("PAT-22", request, SimpleNamespace(id=7))

    assert error.value.status_code == 409
    assert "No database changes were committed" in error.value.detail
    assert db.rolled_back
    assert not db.committed


def test_patient_delete_fails_closed_when_checkpointer_uses_separate_database(monkeypatch):
    db = FakeDeleteDatabase()
    monkeypatch.setattr(report_routes, "db_session_scope", lambda: fake_db_scope(db))
    resources = SimpleNamespace(backend_name="postgres", saver=object())
    settings = SimpleNamespace(
        database_url="postgresql://app:secret@db-one.example:5432/hospital",
        postgres_url="postgresql://app:secret@db-two.example:5432/chat",
    )
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(audio_service=None, checkpointer_resources=resources, settings=settings)
        )
    )

    with pytest.raises(HTTPException) as error:
        report_routes.delete_admin_patient("PAT-22", request, SimpleNamespace(id=7))

    assert error.value.status_code == 503
    assert "same PostgreSQL database" in error.value.detail
    assert not db.statements


def test_same_postgres_database_ignores_driver_and_connection_query_differences():
    assert report_routes._same_postgres_database(
        "postgresql://app:secret@db.example:5432/hospital?sslmode=require",
        "postgresql+psycopg://other:other-secret@DB.EXAMPLE/hospital?connect_timeout=5",
    )


def test_session_activity_lock_uses_transaction_scoped_advisory_lock():
    from services.report_service import acquire_session_activity_lock

    class FakePostgresDatabase:
        def __init__(self):
            self.statements = []
            self.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

        def get_bind(self):
            return self.bind

        def execute(self, statement, params):
            self.statements.append((str(statement), params))

    db = FakePostgresDatabase()
    acquire_session_activity_lock(db, SESSION_ID)

    assert len(db.statements) == 1
    assert "pg_advisory_xact_lock" in db.statements[0][0]
    assert db.statements[0][1] == {"session_id": SESSION_ID}
