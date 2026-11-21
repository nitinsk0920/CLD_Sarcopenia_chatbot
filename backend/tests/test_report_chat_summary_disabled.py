from schemas.report_schemas import FinalReportSaveRequest
from services.report_service import ReportService


class FakeResult:
    def __init__(self, scalar=None):
        self.scalar = scalar

    def mappings(self):
        return self

    def first(self):
        return None

    def scalar_one(self):
        return self.scalar


class FakeDatabase:
    def __init__(self):
        self.statements = []
        self._ids = iter((41, 51, 52, 61))

    def execute(self, statement, params=None):
        sql = str(statement)
        self.statements.append((sql, params or {}))
        if "INSERT INTO patients" in sql:
            scalar = 41
        elif "INSERT INTO quiz_attempts" in sql:
            scalar = next(self._ids)
        elif "INSERT INTO patient_reports" in sql:
            scalar = 61
        else:
            scalar = None
        return FakeResult(scalar)

    def flush(self):
        pass


def test_report_save_ignores_chat_summary_and_keeps_quiz_scores():
    db = FakeDatabase()
    service = ReportService(db)
    payload = FinalReportSaveRequest(
        session_id="00000000-0000-4000-8000-000000000001",
        patient={"patientId": "TEST-1"},
        pre_test={"quiz_type": "pre", "score": 2, "total_questions": 4},
        post_test={"quiz_type": "post", "score": 3, "total_questions": 4},
        short_chat_summary="This legacy value must not be persisted.",
    )

    report_id = service.save_patient_report(payload, admin_id=7)

    assert report_id == "61"
    write_statements = [
        (sql, params)
        for sql, params in db.statements
        if "INSERT INTO patient_sessions" in sql
        or "UPDATE patient_sessions" in sql
        or "INSERT INTO patient_reports" in sql
        or "UPDATE patient_reports" in sql
    ]
    assert write_statements
    assert all("chat_summary" not in sql.lower() for sql, _ in write_statements)
    assert all("chat_summary" not in params for _, params in write_statements)

    report_params = next(params for sql, params in write_statements if "patient_reports" in sql)
    assert report_params["pre_score"] == 2
    assert report_params["post_score"] == 3
