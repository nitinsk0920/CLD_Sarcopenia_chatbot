from __future__ import annotations

import json

import pytest

from chatbot_graph import HealthcareEducationChatbot, _format_patient_context
from schemas.report_schemas import AdminReportDetail, FinalReportSaveRequest, PatientProfilePayload
from services.guardrails import classify_intent
from services.pdf_service import generate_report_pdf
from services.report_service import ReportService


@pytest.mark.parametrize(
    ("question", "language", "label"),
    [
        ("What is my recorded CLD stage?", "en", "Recorded CLD stage"),
        ("मेरी बीमारी का चरण क्या है?", "hi", "दर्ज CLD अवस्था"),
        ("ನನ್ನ ಕಾಯಿಲೆಯ ಹಂತ ಏನು?", "kn", "ದಾಖಲಿಸಿದ CLD ಹಂತ"),
        ("माझ्या आजाराची अवस्था काय?", "mr", "नोंदवलेली CLD अवस्था"),
    ],
)
def test_profile_questions_are_recognized_and_answered_from_session_data(question, language, label):
    assert classify_intent(question) == "patient_profile"
    answer = HealthcareEducationChatbot._profile_reply(
        question, {"cldStage": "compensated_cirrhosis"}, language
    )
    assert label in answer
    assert "compensated cirrhosis" in answer


def test_extended_profile_context_keeps_sensitive_fields_out_of_gemini_context():
    context = _format_patient_context({
        "dietType": "vegetarian",
        "habits": ["smoking"],
        "religion": "hindu",
        "socioeconomicStatus": "socioeconomic_middle",
        "cldStage": "compensated_cirrhosis",
    })
    assert "vegetarian" in context
    assert "smoking" in context
    assert "hindu" not in context
    assert "socioeconomic" not in context
    assert "compensated_cirrhosis" not in context


@pytest.mark.parametrize(
    "question",
    [
        "Do I have any recorded comorbidities?",
        "Have I received nutritional counselling?",
        "Have I previously received CLD education?",
        "What is my socioeconomic status?",
    ],
)
def test_patient_profile_question_variants_are_routed_to_verified_session_data(question):
    assert classify_intent(question) == "patient_profile"


def test_profile_payload_accepts_canonical_registration_fields():
    profile = PatientProfilePayload(
        patientId="PAT-TEST",
        ageGroup="age_31_45",
        gender="female",
        maritalStatus="married",
        familyType="joint",
        residence="rural",
        religion="hindu",
        socioeconomicStatus="socioeconomic_middle",
        cldDuration="one_to_five_years",
        cldEtiology="viral_hepatitis",
        cldStage="compensated_cirrhosis",
        comorbidities=["diabetes", "hypertension"],
        sarcopeniaDuration="not_documented",
        cldTreatment="medical_management_only",
        hospitalizationHistory="once",
        nutritionalCounselling="yes",
        previousHealthEducation="education_cld",
    )
    dumped = profile.model_dump()
    assert dumped["ageGroup"] == "age_31_45"
    assert dumped["comorbidities"] == ["diabetes", "hypertension"]
    assert dumped["cldStage"] == "compensated_cirrhosis"


class _Result:
    def __init__(self, row=None):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class _CaptureDb:
    def __init__(self):
        self.calls = []

    def execute(self, statement, params=None):
        self.calls.append((str(statement), params or {}))
        class InsertResult(_Result):
            def scalar_one(self):
                return 19
        return InsertResult()


def test_completed_session_persists_final_profile_snapshot_in_existing_jsonb():
    db = _CaptureDb()
    payload = FinalReportSaveRequest(
        session_id="00000000-0000-4000-8000-000000000001",
        patient={"patientId": "PAT-TEST", "ageGroup": "age_31_45", "habits": ["smoking"]},
        pre_test={"quiz_type": "pre", "score": 2, "total_questions": 4},
        post_test={"quiz_type": "post", "score": 3, "total_questions": 4},
    )
    ReportService(db)._upsert_patient_session_for_report(
        payload, admin_id=7, patient_id=3, learning_summary=""
    )
    sql, params = db.calls[-1]
    snapshot = json.loads(params["draft_profile"])
    assert "draft_profile" in sql
    assert "CAST(:draft_profile AS jsonb)" in sql
    assert snapshot["fields"]["ageGroup"] == "age_31_45"
    assert snapshot["fields"]["habits"] == ["smoking"]


def test_new_draft_session_saves_all_profile_fields_and_selected_language():
    db = _CaptureDb()
    profile = PatientProfilePayload(
        patientId="PAT-DRAFT",
        languagePreference="kn",
        ageGroup="age_46_60",
        cldStage="not_documented",
        comorbidities=["no_known_comorbidities"],
        cldEtiologyOther="",
    )
    ReportService(db).start_draft_session(
        "00000000-0000-4000-8000-000000000002", profile, admin_id=7
    )
    insert_sql, params = db.calls[-1]
    saved = json.loads(params["draft_profile"])
    assert "INSERT INTO patient_sessions" in insert_sql
    assert params["selected_language"] == "kn"
    assert saved["fields"]["ageGroup"] == "age_46_60"
    assert saved["fields"]["comorbidities"] == ["no_known_comorbidities"]


def test_active_session_resume_returns_saved_multilingual_profile_fields():
    saved_fields = {
        "languagePreference": "mr",
        "ageGroup": "age_61_plus",
        "cldStage": "decompensated_cirrhosis",
        "cldTreatmentOther": "Recorded text",
    }

    class ResumeDb:
        def execute(self, *_args, **_kwargs):
            return _Result({"draft_profile": {"fields": saved_fields}})

    result = ReportService(ResumeDb()).get_active_session_profile(
        "00000000-0000-4000-8000-000000000002", admin_id=7
    )
    assert result["languagePreference"] == "mr"
    assert result["ageGroup"] == "age_61_plus"
    assert result["cldTreatmentOther"] == "Recorded text"


def test_pdf_generation_includes_registration_sections():
    try:
        report = AdminReportDetail(
            report_id="1",
            session_id="00000000-0000-4000-8000-000000000001",
            patient={
                "patient_id": "PAT-TEST",
                "ageGroup": "age_31_45",
                "maritalStatus": "married",
                "cldDuration": "one_to_five_years",
                "comorbidities": ["diabetes"],
            },
            session={"session_id": "00000000-0000-4000-8000-000000000001"},
            report={"completion_status": "completed", "pre_test_score": 2, "post_test_score": 3},
        )
        pdf = generate_report_pdf(report)
    except RuntimeError as exc:
        if "reportlab" in str(exc):
            pytest.skip("reportlab is not installed in the test environment")
        raise
    assert pdf.startswith(b"%PDF")
