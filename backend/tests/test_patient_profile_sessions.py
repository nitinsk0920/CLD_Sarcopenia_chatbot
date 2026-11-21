from __future__ import annotations

from datetime import datetime, timezone

from services.report_service import ReportService


class _Mappings:
    def __init__(self, row):
        self.row = row

    def first(self):
        return self.row


class _Result:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return _Mappings(self.row)


class _ProfileDb:
    def __init__(self, row):
        self.row = row
        self.params = None
        self.statement = ""

    def execute(self, statement, params):
        self.statement = str(statement)
        self.params = params
        return _Result(self.row)


def test_session_profile_lookup_is_bound_to_authenticated_admin_and_active_session():
    row = {
        "draft_profile": {"fields": {"age": 63, "dietType": "vegetarian", "habits": ["smoking"]}},
        "patient_code": "P-ONLY-IN-SESSION",
    }
    db = _ProfileDb(row)

    result = ReportService(db).get_active_session_profile(
        "56d21e14-3a25-4521-8a65-19dbbe4ca279", admin_id=42
    )

    assert result == {"age": 63, "dietType": "vegetarian", "habits": ["smoking"]}
    assert db.params == {"session_id": "56d21e14-3a25-4521-8a65-19dbbe4ca279", "admin_id": 42}
    assert "ps.admin_id = :admin_id" in db.statement
    assert "ps.status = 'active'" in db.statement
    assert "patient_sessions ps" in db.statement
    assert "JOIN patients p ON p.id = ps.patient_id" in db.statement


def test_profile_lookup_returns_none_when_session_is_not_owned_or_active():
    db = _ProfileDb(None)
    result = ReportService(db).get_active_session_profile(
        "56d21e14-3a25-4521-8a65-19dbbe4ca279", admin_id=9001
    )
    assert result is None
    assert db.params["admin_id"] == 9001


def test_active_session_state_restores_saved_profile_and_start_time():
    started_at = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)
    row = {
        "started_at": started_at,
        "draft_profile": {"fields": {"age": 63, "languagePreference": "hi"}},
    }
    result = ReportService(_ProfileDb(row)).get_active_session_state(
        "56d21e14-3a25-4521-8a65-19dbbe4ca279", admin_id=42
    )
    assert result == {
        "session_id": "56d21e14-3a25-4521-8a65-19dbbe4ca279",
        "started_at": started_at,
        "patient": {"age": 63, "languagePreference": "hi"},
    }
