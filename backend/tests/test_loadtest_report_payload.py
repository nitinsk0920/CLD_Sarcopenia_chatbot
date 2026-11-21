import json
from pathlib import Path

from schemas.report_schemas import FinalReportSaveRequest
from services.report_service import ReportService
from loadtest.config import build_report_save_payload


TEST_DATA_PATH = Path(__file__).resolve().parents[1] / "loadtest" / "test_data.json"


class _Mappings:
    def __init__(self, row=None):
        self.row = row

    def first(self):
        return self.row


class _Result:
    def __init__(self, scalar=None, mappings_row=None):
        self.scalar = scalar
        self.mappings_row = mappings_row

    def mappings(self):
        return _Mappings(self.mappings_row)

    def scalar_one(self):
        return self.scalar


class _ReportSaveDb:
    def __init__(self, session_id, admin_id):
        self.statements = []
        self.quiz_ids = iter((51, 52))
        self.session_id = session_id
        self.admin_id = admin_id

    def execute(self, statement, params=None):
        sql = str(statement)
        params = params or {}
        self.statements.append((sql, params))
        if "SELECT id, admin_id" in sql and "FROM patient_sessions" in sql:
            return _Result(mappings_row={"id": self.session_id, "admin_id": self.admin_id})
        if "INSERT INTO patients" in sql:
            return _Result(41)
        if "INSERT INTO quiz_attempts" in sql:
            return _Result(next(self.quiz_ids))
        if "INSERT INTO patient_reports" in sql:
            return _Result(61)
        return _Result()

    def flush(self):
        pass


def test_exact_locust_report_payload_saves_via_existing_report_service():
    test_data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    session_id = "00000000-0000-4000-8000-000000000091"
    patient = {**test_data["patient_profile"], "patientId": "LOADTEST-a1b2c3d4-regression"}
    payload_data = build_report_save_payload(
        session_id=session_id,
        patient=patient,
        quiz=test_data["quiz"],
        session_started_at="2026-11-21T12:00:00+00:00",
    )

    payload = FinalReportSaveRequest.model_validate(payload_data)
    db = _ReportSaveDb(session_id, admin_id=17)
    report_id = ReportService(db).save_patient_report(payload, admin_id=17)

    assert report_id == "61"
    assert payload.pre_test.quiz_type == "pre"
    assert payload.post_test.quiz_type == "post"
    assert payload.pre_test.score == 2
    assert payload.post_test.score == 3
    assert len(payload.pre_test.answers) == len(payload.post_test.answers) == 4

    quiz_writes = [params for sql, params in db.statements if "INSERT INTO quiz_attempts" in sql]
    assert [params["quiz_type"] for params in quiz_writes] == ["pre", "post"]
    assert any("UPDATE patient_sessions" in sql for sql, _ in db.statements)
    report_params = next(params for sql, params in db.statements if "INSERT INTO patient_reports" in sql)
    assert report_params["patient_code"] == patient["patientId"]
    assert report_params["pre_score"] == 2
    assert report_params["post_score"] == 3
    assert report_params["educational_qualification"] == patient["educationalQualification"]
    assert report_params["occupation"] == patient["occupation"]
