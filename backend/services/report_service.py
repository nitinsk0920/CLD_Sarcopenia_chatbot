from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from typing import Any

from sqlalchemy import bindparam
from sqlalchemy import text
from sqlalchemy.orm import Session

from schemas.report_schemas import AdminQuizAttemptDetail
from schemas.report_schemas import AdminReportDetail
from schemas.report_schemas import AdminReportListItem
from schemas.report_schemas import FinalReportSaveRequest
from schemas.report_schemas import PatientProfilePayload
from schemas.report_schemas import QuizAttemptPayload


def acquire_session_activity_lock(db: Session, session_id: str) -> None:
    """Serialize chat generation and destructive operations for a session in PostgreSQL."""
    get_bind = getattr(db, "get_bind", None)
    bind = get_bind() if callable(get_bind) else None
    if getattr(getattr(bind, "dialect", None), "name", None) != "postgresql":
        return
    db.execute(
        text("SELECT pg_advisory_xact_lock(0, hashtext(:session_id))"),
        {"session_id": str(session_id)},
    )


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _habit_text(enabled: bool) -> str:
        return "yes" if enabled else "no"

    def has_active_session(self, session_id: str, *, admin_id: int) -> bool:
        row = self.db.execute(text("""
            SELECT id
            FROM patient_sessions
            WHERE id = CAST(:session_id AS uuid)
              AND admin_id = :admin_id
              AND status = 'active'
            LIMIT 1
        """), {"session_id": session_id, "admin_id": admin_id}).first()
        return row is not None

    def get_active_session_profile(
        self,
        session_id: str,
        *,
        admin_id: int,
    ) -> dict[str, Any] | None:
        """Return the saved profile only for this admin's active, patient-linked session."""
        row = (
            self.db.execute(
                text(
                    """
                    SELECT
                        ps.draft_profile,
                        p.patient_code,
                        p.age,
                        p.gender,
                        p.educational_qualification,
                        p.occupation,
                        p.diet_type,
                        p.alcohol_habit,
                        p.smoking_habit,
                        p.language,
                        p.cld_status,
                        p.exercise_habit,
                        p.symptoms
                    FROM patient_sessions ps
                    JOIN patients p ON p.id = ps.patient_id
                                    AND p.admin_id = ps.admin_id
                    WHERE ps.id = CAST(:session_id AS uuid)
                      AND ps.admin_id = :admin_id
                      AND ps.status = 'active'
                    LIMIT 1
                    """
                ),
                {"session_id": session_id, "admin_id": admin_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None

        draft_profile = row.get("draft_profile")
        if isinstance(draft_profile, str):
            try:
                draft_profile = json.loads(draft_profile)
            except (TypeError, ValueError):
                draft_profile = None

        if isinstance(draft_profile, dict):
            draft_fields = draft_profile.get("fields", draft_profile)
            profile = dict(draft_fields) if isinstance(draft_fields, dict) else {}
        else:
            profile = {}

        patient_fields = {
            "age": row.get("age"),
            "gender": row.get("gender"),
            "educationalQualification": row.get("educational_qualification"),
            "occupation": row.get("occupation"),
            "dietType": row.get("diet_type"),
            "languagePreference": row.get("language"),
            "cldStatus": row.get("cld_status"),
            "exerciseRegular": row.get("exercise_habit"),
            "symptoms": row.get("symptoms"),
        }
        habits = [
            name
            for name, value in (
                ("alcohol", row.get("alcohol_habit")),
                ("smoking", row.get("smoking_habit")),
            )
            if str(value or "").strip().lower() in {"yes", "true", "1"}
        ]
        if habits:
            patient_fields["habits"] = habits

        for key, value in patient_fields.items():
            if value not in (None, "", []) and profile.get(key) in (None, "", []):
                profile[key] = value

        return profile or None

    def get_active_session_state(
        self,
        session_id: str,
        *,
        admin_id: int,
    ) -> dict[str, Any] | None:
        row = (
            self.db.execute(
                text(
                    """
                    SELECT started_at
                    FROM patient_sessions
                    WHERE id = CAST(:session_id AS uuid)
                      AND admin_id = :admin_id
                      AND status = 'active'
                    LIMIT 1
                    """
                ),
                {"session_id": session_id, "admin_id": admin_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        profile = self.get_active_session_profile(session_id, admin_id=admin_id)
        if profile is None:
            return None
        return {"session_id": session_id, "started_at": row.get("started_at"), "patient": profile}

    def start_draft_session(
        self,
        session_id: str,
        payload: PatientProfilePayload,
        *,
        admin_id: int,
        started_at: datetime | None = None,
    ) -> dict[str, Any]:
        """Persist a draft on an admin-owned active session without replacing saved patients."""
        started_at = self._ensure_aware_datetime(started_at or datetime.now(timezone.utc))
        draft_json = json.dumps({"fields": payload.model_dump(exclude_none=True)})
        existing = (
            self.db.execute(
                text(
                    """
                    SELECT admin_id, patient_id, status
                    FROM patient_sessions
                    WHERE id = CAST(:session_id AS uuid)
                    LIMIT 1
                    """
                ),
                {"session_id": session_id},
            )
            .mappings()
            .first()
        )
        if existing is not None:
            if int(existing["admin_id"]) != admin_id:
                raise ValueError("This session belongs to another hospital account.")
            if existing.get("status") != "active":
                raise ValueError("This patient session is no longer active.")
            self.db.execute(
                text(
                    """
                    UPDATE patient_sessions
                    SET draft_profile = CAST(:draft_profile AS jsonb),
                        selected_language = :selected_language,
                        updated_at = :updated_at
                    WHERE id = CAST(:session_id AS uuid) AND admin_id = :admin_id
                    """
                ),
                {
                    "session_id": session_id,
                    "admin_id": admin_id,
                    "draft_profile": draft_json,
                    "selected_language": payload.languagePreference,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            return {"session_id": session_id, "patient_id": payload.patientId}

        patient_row = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM patients
                    WHERE admin_id = :admin_id AND patient_code = :patient_code
                    LIMIT 1
                    """
                ),
                {"admin_id": admin_id, "patient_code": payload.patientId},
            )
            .mappings()
            .first()
        )
        if patient_row is None:
            placeholder_code = f"__draft__:{session_id}"
            patient_id = self.db.execute(
                text(
                    """
                    INSERT INTO patients (admin_id, patient_code, created_at, updated_at)
                    VALUES (:admin_id, :patient_code, :created_at, :updated_at)
                    RETURNING id
                    """
                ),
                {
                    "admin_id": admin_id,
                    "patient_code": placeholder_code,
                    "created_at": started_at,
                    "updated_at": started_at,
                },
            ).scalar_one()
        else:
            patient_id = patient_row["id"]

        self.db.execute(
            text(
                """
                INSERT INTO patient_sessions (
                    id, admin_id, patient_id, status, selected_language,
                    draft_profile, started_at, updated_at
                )
                VALUES (
                    CAST(:session_id AS uuid), :admin_id, :patient_id, 'active',
                    :selected_language, CAST(:draft_profile AS jsonb), :started_at, :updated_at
                )
                """
            ),
            {
                "session_id": session_id,
                "admin_id": admin_id,
                "patient_id": patient_id,
                "selected_language": payload.languagePreference,
                "draft_profile": draft_json,
                "started_at": started_at,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return {"session_id": session_id, "patient_id": payload.patientId}

    def discard_draft_session(self, session_id: str, *, admin_id: int) -> bool:
        row = (
            self.db.execute(
                text(
                    """
                    SELECT ps.patient_id, p.patient_code
                    FROM patient_sessions ps
                    JOIN patients p ON p.id = ps.patient_id AND p.admin_id = ps.admin_id
                    WHERE ps.id = CAST(:session_id AS uuid)
                      AND ps.admin_id = :admin_id
                      AND ps.status = 'active'
                    LIMIT 1
                    """
                ),
                {"session_id": session_id, "admin_id": admin_id},
            )
            .mappings()
            .first()
        )
        if row is None:
            return False

        self.db.execute(
            text(
                """
                DELETE FROM patient_sessions
                WHERE id = CAST(:session_id AS uuid) AND admin_id = :admin_id AND status = 'active'
                """
            ),
            {"session_id": session_id, "admin_id": admin_id},
        )
        if row.get("patient_code") == f"__draft__:{session_id}":
            self.db.execute(
                text(
                    """
                    DELETE FROM patients p
                    WHERE p.id = :patient_id AND p.admin_id = :admin_id
                      AND p.patient_code = :placeholder_code
                      AND NOT EXISTS (SELECT 1 FROM patient_sessions ps WHERE ps.patient_id = p.id)
                      AND NOT EXISTS (SELECT 1 FROM patient_reports pr WHERE pr.patient_id = p.id)
                    """
                ),
                {
                    "patient_id": row["patient_id"],
                    "admin_id": admin_id,
                    "placeholder_code": f"__draft__:{session_id}",
                },
            )
        return True

    def create_patient_record(self, payload: PatientProfilePayload, *, admin_id: int) -> dict[str, Any]:
        patient_id = self._get_or_create_patient_for_report(payload, admin_id=admin_id)
        return {
            "id": patient_id,
            "patient_id": payload.patientId,
            "language": payload.languagePreference,
        }

    def create_session(
        self,
        session_id: str,
        patient: dict[str, Any],
        *,
        admin_id: int,
        started_at: datetime | None = None,
    ) -> dict[str, Any]:
        started_at = self._ensure_aware_datetime(started_at or datetime.now(timezone.utc))
        selected_language = str(patient.get("language") or "")
        existing = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM patient_sessions
                    WHERE id = CAST(:session_id AS uuid) AND admin_id = :admin_id
                    LIMIT 1
                    """
                ),
                {"session_id": session_id, "admin_id": admin_id},
            )
            .mappings()
            .first()
        )

        params = {
            "session_id": session_id,
            "admin_id": admin_id,
            "patient_id": int(patient["id"]),
            "status": "active",
            "selected_language": selected_language or None,
            "started_at": started_at,
            "updated_at": datetime.now(timezone.utc),
        }

        if existing is None:
            self.db.execute(
                text(
                    """
                    INSERT INTO patient_sessions (
                        id,
                        admin_id,
                        patient_id,
                        status,
                        selected_language,
                        started_at,
                        updated_at
                    )
                    VALUES (
                        CAST(:session_id AS uuid),
                        :admin_id,
                        :patient_id,
                        :status,
                        :selected_language,
                        :started_at,
                        :updated_at
                    )
                    """
                ),
                params,
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE patient_sessions
                    SET
                        patient_id = :patient_id,
                        selected_language = COALESCE(:selected_language, selected_language),
                        started_at = COALESCE(started_at, :started_at),
                        updated_at = :updated_at
                    WHERE id = CAST(:session_id AS uuid) AND admin_id = :admin_id
                    """
                ),
                params,
            )

        return {"session_id": session_id}

    def end_session(
        self,
        session_id: str,
        *,
        admin_id: int,
        ended_at: datetime | None = None,
        completion_status: str = "completed",
    ) -> dict[str, Any]:
        ended_at = self._ensure_aware_datetime(ended_at or datetime.now(timezone.utc))
        result = self.db.execute(
            text(
                """
                UPDATE patient_sessions
                SET
                    status = :status,
                    ended_at = :ended_at,
                    updated_at = :updated_at
                WHERE id = CAST(:session_id AS uuid) AND admin_id = :admin_id
                """
            ),
            {
                "session_id": session_id,
                "admin_id": admin_id,
                "status": completion_status,
                "ended_at": ended_at,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        if result.rowcount == 0:
            raise ValueError(f"Session {session_id} was not found.")
        return {"session_id": session_id}

    def _upsert_quiz_attempt(
        self,
        session_id: str,
        payload: QuizAttemptPayload,
    ) -> int:
        existing_attempt = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM quiz_attempts
                    WHERE session_id = CAST(:session_id AS uuid) AND quiz_type = :quiz_type
                    LIMIT 1
                    """
                ),
                {
                    "session_id": session_id,
                    "quiz_type": payload.quiz_type,
                },
            )
            .mappings()
            .first()
        )

        params = {
            "session_id": session_id,
            "quiz_type": payload.quiz_type,
            "total_questions": payload.total_questions,
            "correct_answers": sum(1 for answer in payload.answers if answer.is_correct),
            "score": payload.score,
            "score_level": payload.score_level,
            "weak_topics": payload.weak_topics or [],
            "created_at": self._ensure_aware_datetime(payload.submitted_at or datetime.now(timezone.utc)),
        }

        if existing_attempt is None:
            attempt_id = int(
                self.db.execute(
                    text(
                        """
                        INSERT INTO quiz_attempts (
                            session_id,
                            quiz_type,
                            total_questions,
                            correct_answers,
                            score,
                            score_level,
                            weak_topics,
                            created_at
                        )
                        VALUES (
                            CAST(:session_id AS uuid),
                            :quiz_type,
                            :total_questions,
                            :correct_answers,
                            :score,
                            :score_level,
                            :weak_topics,
                            :created_at
                        )
                        RETURNING id
                        """
                    ),
                    params,
                ).scalar_one()
            )
        else:
            attempt_id = int(existing_attempt["id"])
            self.db.execute(
                text(
                    """
                    UPDATE quiz_attempts
                    SET
                        total_questions = :total_questions,
                        correct_answers = :correct_answers,
                        score = :score,
                        score_level = :score_level,
                        weak_topics = :weak_topics,
                        created_at = :created_at
                    WHERE id = :attempt_id
                    """
                ),
                {
                    **params,
                    "attempt_id": attempt_id,
                },
            )
            self.db.execute(
                text("DELETE FROM quiz_answers WHERE quiz_attempt_id = :attempt_id"),
                {"attempt_id": attempt_id},
            )

        for answer in payload.answers:
            self.db.execute(
                text(
                    """
                    INSERT INTO quiz_answers (
                        quiz_attempt_id,
                        question_number,
                        question_text,
                        selected_answer,
                        correct_answer,
                        is_correct,
                        topic,
                        explanation,
                        created_at
                    )
                    VALUES (
                        :quiz_attempt_id,
                        :question_number,
                        :question_text,
                        :selected_answer,
                        :correct_answer,
                        :is_correct,
                        :topic,
                        :explanation,
                        :created_at
                    )
                    """
                ),
                {
                    "quiz_attempt_id": attempt_id,
                    "question_number": answer.question_id,
                    "question_text": answer.question_text,
                    "selected_answer": answer.selected_answer,
                    "correct_answer": answer.correct_answer,
                    "is_correct": answer.is_correct,
                    "topic": answer.topic,
                    "explanation": answer.explanation,
                    "created_at": self._ensure_aware_datetime(
                        payload.submitted_at or datetime.now(timezone.utc)
                    ),
                },
            )

        return attempt_id

    def _build_learning_summary(self, payload: FinalReportSaveRequest) -> str:
        if payload.learning_summary.strip():
            return payload.learning_summary.strip()

        pre_weak = payload.pre_test.weak_topics or []
        post_weak = payload.post_test.weak_topics or []
        improvement = payload.post_test.score - payload.pre_test.score
        focus_text = ", ".join(pre_weak) if pre_weak else "general review"
        remaining_text = ", ".join(post_weak) if post_weak else "no major weak topics remained"
        return (
            f"Patient completed the guided CLD and sarcopenia learning flow. "
            f"Main focus areas were {focus_text}. "
            f"Score improvement was {improvement} points. "
            f"After learning, {remaining_text}."
        )

    def _build_key_misconceptions(self, payload: FinalReportSaveRequest) -> list[str]:
        misconceptions = [
            answer.question_text
            for answer in payload.pre_test.answers
            if not answer.is_correct
        ]
        return misconceptions[:8]

    def _resolve_strong_topics(self, payload: FinalReportSaveRequest) -> list[str]:
        if payload.post_test.strong_topics:
            return payload.post_test.strong_topics

        post_summary = payload.post_test.summary or {}
        mistakes_by_topic = post_summary.get("mistakesByTopic", {})
        return sorted([topic for topic, count in mistakes_by_topic.items() if count == 0])

    @staticmethod
    def _ensure_aware_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def _get_or_create_patient_for_report(
        self,
        payload: PatientProfilePayload,
        *,
        admin_id: int,
    ) -> int:
        habits = {item.lower() for item in (payload.habits or [])}
        patient_row = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM patients
                    WHERE admin_id = :admin_id AND patient_code = :patient_code
                    LIMIT 1
                    """
                ),
                {
                    "admin_id": admin_id,
                    "patient_code": payload.patientId,
                },
            )
            .mappings()
            .first()
        )

        params = {
            "admin_id": admin_id,
            "patient_code": payload.patientId,
            "age": payload.age,
            "gender": payload.gender,
            "educational_qualification": payload.educationalQualification,
            "occupation": payload.occupation,
            "diet_type": payload.dietType,
            "alcohol_habit": self._habit_text("alcohol" in habits),
            "smoking_habit": self._habit_text("smoking" in habits),
            "language": payload.languagePreference,
            "cld_status": payload.cldStatus,
            "exercise_habit": payload.exerciseRegular,
            "symptoms": payload.symptoms or [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        if patient_row is None:
            created = (
                self.db.execute(
                    text(
                        """
                        INSERT INTO patients (
                            admin_id,
                            patient_code,
                            age,
                            gender,
                            educational_qualification,
                            occupation,
                            diet_type,
                            alcohol_habit,
                            smoking_habit,
                            language,
                            cld_status,
                            exercise_habit,
                            symptoms,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :admin_id,
                            :patient_code,
                            :age,
                            :gender,
                            :educational_qualification,
                            :occupation,
                            :diet_type,
                            :alcohol_habit,
                            :smoking_habit,
                            :language,
                            :cld_status,
                            :exercise_habit,
                            :symptoms,
                            :created_at,
                            :updated_at
                        )
                        RETURNING id
                        """
                    ),
                    params,
                )
                .scalar_one()
            )
            return int(created)

        patient_id = int(patient_row["id"])
        self.db.execute(
            text(
                """
                UPDATE patients
                SET
                    age = :age,
                    gender = :gender,
                    educational_qualification = :educational_qualification,
                    occupation = :occupation,
                    diet_type = :diet_type,
                    alcohol_habit = :alcohol_habit,
                    smoking_habit = :smoking_habit,
                    language = :language,
                    cld_status = :cld_status,
                    exercise_habit = :exercise_habit,
                    symptoms = :symptoms,
                    updated_at = :updated_at
                WHERE id = :patient_id
                """
            ),
            {
                **params,
                "patient_id": patient_id,
            },
        )
        return patient_id

    def _upsert_patient_session_for_report(
        self,
        payload: FinalReportSaveRequest,
        *,
        admin_id: int,
        patient_id: int,
        learning_summary: str,
    ) -> str:
        started_at = self._ensure_aware_datetime(
            payload.session_started_at or datetime.now(timezone.utc)
        )
        ended_at = self._ensure_aware_datetime(
            payload.session_ended_at or datetime.now(timezone.utc)
        )
        weak_topics = payload.pre_test.weak_topics or []
        selected_language = payload.patient.languagePreference

        existing = (
            self.db.execute(
                text(
                    """
                    SELECT id, admin_id
                    FROM patient_sessions
                    WHERE id = CAST(:session_id AS uuid)
                    LIMIT 1
                    """
                ),
                {"session_id": payload.session_id},
            )
            .mappings()
            .first()
        )

        params = {
            "session_id": payload.session_id,
            "admin_id": admin_id,
            "patient_id": patient_id,
            "status": payload.completion_status,
            "selected_language": selected_language,
            "draft_profile": json.dumps({"fields": payload.patient.model_dump(exclude_none=True)}),
            "learning_summary": learning_summary,
            "weak_topics": weak_topics,
            "started_at": started_at,
            "ended_at": ended_at,
            "updated_at": datetime.now(timezone.utc),
        }

        if existing is not None and int(existing["admin_id"]) != admin_id:
            raise ValueError("This session belongs to another hospital account.")

        if existing is None:
            self.db.execute(
                text(
                    """
                    INSERT INTO patient_sessions (
                        id,
                        admin_id,
                        patient_id,
                        status,
                        selected_language,
                        draft_profile,
                        learning_summary,
                        weak_topics,
                        started_at,
                        ended_at,
                        updated_at
                    )
                    VALUES (
                        CAST(:session_id AS uuid),
                        :admin_id,
                        :patient_id,
                        :status,
                        :selected_language,
                        CAST(:draft_profile AS jsonb),
                        :learning_summary,
                        :weak_topics,
                        :started_at,
                        :ended_at,
                        :updated_at
                    )
                    """
                ),
                params,
            )
        else:
            self.db.execute(
                text(
                    """
                    UPDATE patient_sessions
                    SET
                        patient_id = :patient_id,
                        status = :status,
                        selected_language = :selected_language,
                        draft_profile = CAST(:draft_profile AS jsonb),
                        learning_summary = :learning_summary,
                        weak_topics = :weak_topics,
                        started_at = COALESCE(started_at, :started_at),
                        ended_at = :ended_at,
                        updated_at = :updated_at
                    WHERE id = CAST(:session_id AS uuid)
                    """
                ),
                params,
            )

        return payload.session_id

    def save_patient_report(self, payload: FinalReportSaveRequest, *, admin_id: int) -> str:
        patient_id = self._get_or_create_patient_for_report(payload.patient, admin_id=admin_id)
        learning_summary = self._build_learning_summary(payload)
        session_id = self._upsert_patient_session_for_report(
            payload,
            admin_id=admin_id,
            patient_id=patient_id,
            learning_summary=learning_summary,
        )
        self._upsert_quiz_attempt(session_id, payload.pre_test)
        self._upsert_quiz_attempt(session_id, payload.post_test)

        started_at = self._ensure_aware_datetime(
            payload.session_started_at or datetime.now(timezone.utc)
        )
        ended_at = self._ensure_aware_datetime(
            payload.session_ended_at or datetime.now(timezone.utc)
        )
        duration_minutes = None
        if started_at and ended_at:
            duration_minutes = max(0, int((ended_at - started_at).total_seconds() // 60))

        improvement = payload.post_test.score - payload.pre_test.score
        existing_report = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM patient_reports
                    WHERE session_id = CAST(:session_id AS uuid)
                    LIMIT 1
                    """
                ),
                {"session_id": session_id},
            )
            .mappings()
            .first()
        )

        params = {
            "admin_id": admin_id,
            "patient_id": patient_id,
            "session_id": session_id,
            "patient_code": payload.patient.patientId,
            "age": payload.patient.age,
            "gender": payload.patient.gender,
            "educational_qualification": payload.patient.educationalQualification,
            "occupation": payload.patient.occupation,
            "diet_type": payload.patient.dietType,
            "alcohol_habit": self._habit_text("alcohol" in {item.lower() for item in (payload.patient.habits or [])}),
            "smoking_habit": self._habit_text("smoking" in {item.lower() for item in (payload.patient.habits or [])}),
            "language": payload.patient.languagePreference,
            "cld_status": payload.patient.cldStatus,
            "exercise_habit": payload.patient.exerciseRegular,
            "symptoms": payload.patient.symptoms or [],
            "session_started_at": started_at,
            "session_ended_at": ended_at,
            "session_duration_minutes": duration_minutes,
            "pre_score": payload.pre_test.score,
            "post_score": payload.post_test.score,
            "improvement": improvement,
            "pre_score_level": payload.pre_test.score_level,
            "post_score_level": payload.post_test.score_level,
            "weak_topics": payload.pre_test.weak_topics or [],
            "learning_summary": learning_summary,
            "completion_status": payload.completion_status,
            "updated_at": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
        }

        if existing_report is None:
            report_id = (
                self.db.execute(
                    text(
                        """
                        INSERT INTO patient_reports (
                            admin_id,
                            patient_id,
                            session_id,
                            patient_code,
                            age,
                            gender,
                            educational_qualification,
                            occupation,
                            diet_type,
                            alcohol_habit,
                            smoking_habit,
                            language,
                            cld_status,
                            exercise_habit,
                            symptoms,
                            session_started_at,
                            session_ended_at,
                            session_duration_minutes,
                            pre_score,
                            post_score,
                            improvement,
                            pre_score_level,
                            post_score_level,
                            weak_topics,
                            learning_summary,
                            completion_status,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :admin_id,
                            :patient_id,
                            CAST(:session_id AS uuid),
                            :patient_code,
                            :age,
                            :gender,
                            :educational_qualification,
                            :occupation,
                            :diet_type,
                            :alcohol_habit,
                            :smoking_habit,
                            :language,
                            :cld_status,
                            :exercise_habit,
                            :symptoms,
                            :session_started_at,
                            :session_ended_at,
                            :session_duration_minutes,
                            :pre_score,
                            :post_score,
                            :improvement,
                            :pre_score_level,
                            :post_score_level,
                            :weak_topics,
                            :learning_summary,
                            :completion_status,
                            :created_at,
                            :updated_at
                        )
                        RETURNING id
                        """
                    ),
                    params,
                )
                .scalar_one()
            )
            self.db.flush()
            return str(report_id)

        report_id = existing_report["id"]
        self.db.execute(
            text(
                """
                UPDATE patient_reports
                SET
                    admin_id = :admin_id,
                    patient_id = :patient_id,
                    patient_code = :patient_code,
                    age = :age,
                    gender = :gender,
                    educational_qualification = :educational_qualification,
                    occupation = :occupation,
                    diet_type = :diet_type,
                    alcohol_habit = :alcohol_habit,
                    smoking_habit = :smoking_habit,
                    language = :language,
                    cld_status = :cld_status,
                    exercise_habit = :exercise_habit,
                    symptoms = :symptoms,
                    session_started_at = :session_started_at,
                    session_ended_at = :session_ended_at,
                    session_duration_minutes = :session_duration_minutes,
                    pre_score = :pre_score,
                    post_score = :post_score,
                    improvement = :improvement,
                    pre_score_level = :pre_score_level,
                    post_score_level = :post_score_level,
                    weak_topics = :weak_topics,
                    learning_summary = :learning_summary,
                    completion_status = :completion_status,
                    updated_at = :updated_at
                WHERE session_id = CAST(:session_id AS uuid)
                """
            ),
            params,
        )
        self.db.flush()
        return str(report_id)

    def save_final_session_report(self, payload: FinalReportSaveRequest, *, admin_id: int) -> str:
        return self.save_patient_report(payload, admin_id=admin_id)

    def _attempt_to_schema(self, attempt: dict[str, Any] | None) -> AdminQuizAttemptDetail | None:
        if attempt is None:
            return None
        return AdminQuizAttemptDetail(
            quiz_type=str(attempt.get("quiz_type")),
            score=int(attempt.get("score") or 0),
            total_questions=int(attempt.get("total_questions") or 0),
            score_level=attempt.get("score_level"),
            weak_topics=attempt.get("weak_topics") or [],
            strong_topics=[],
            submitted_at=attempt.get("created_at"),
            answers=[
                {
                    "question_id": int(answer.get("question_number") or 0),
                    "question_text": answer.get("question_text"),
                    "topic": answer.get("topic"),
                    "selected_answer": answer.get("selected_answer"),
                    "correct_answer": answer.get("correct_answer"),
                    "is_correct": answer.get("is_correct"),
                    "explanation": answer.get("explanation"),
                }
                for answer in sorted(attempt.get("answers") or [], key=lambda item: item.get("question_number") or 0)
            ],
        )

    def _mapping_attempt_to_schema(
        self,
        attempt: dict | None,
        answers: list[dict],
    ) -> AdminQuizAttemptDetail | None:
        if attempt is None:
            return None

        return AdminQuizAttemptDetail(
            quiz_type=attempt["quiz_type"],
            score=attempt["score"],
            total_questions=attempt["total_questions"],
            score_level=attempt.get("score_level"),
            weak_topics=attempt.get("weak_topics") or [],
            strong_topics=[],
            submitted_at=attempt.get("created_at"),
            answers=[
                {
                    "question_id": answer.get("question_number") or 0,
                    "question_text": answer.get("question_text"),
                    "topic": answer.get("topic"),
                    "selected_answer": answer.get("selected_answer"),
                    "correct_answer": answer.get("correct_answer"),
                    "is_correct": answer.get("is_correct"),
                    "explanation": answer.get("explanation"),
                }
                for answer in sorted(answers, key=lambda item: item.get("question_number") or 0)
            ],
        )

    def fetch_all_reports_for_admin(self, admin_id: int) -> list[AdminReportListItem]:
        reports = (
            self.db.execute(
                text(
                    """
                    SELECT
                        id,
                        session_id,
                        patient_code,
                        age,
                        gender,
                        language,
                        pre_score,
                        post_score,
                        improvement,
                        weak_topics,
                        completion_status,
                        session_started_at,
                        session_ended_at,
                        COALESCE(updated_at, created_at, session_ended_at, session_started_at) AS report_date
                    FROM patient_reports
                    WHERE admin_id = :admin_id
                    ORDER BY COALESCE(updated_at, created_at, session_ended_at, session_started_at) DESC, id DESC
                    """
                ),
                {"admin_id": admin_id},
            )
            .mappings()
            .all()
        )
        return [
            AdminReportListItem(
                report_id=str(report["id"]),
                session_id=str(report["session_id"]),
                patient_id=report["patient_code"],
                patient_code=report["patient_code"],
                age=report["age"],
                gender=report["gender"],
                language=report["language"],
                pre_test_score=report["pre_score"],
                post_test_score=report["post_score"],
                score=report["post_score"],
                improvement=report["improvement"],
                weak_topics=report["weak_topics"] or [],
                completion_status=report["completion_status"],
                session_start_time=report["session_started_at"],
                session_end_time=report["session_ended_at"],
                report_date=report["report_date"],
            )
            for report in reports
        ]

    def delete_patient_data(self, patient_code: str, *, admin_id: int) -> dict[str, Any]:
        """Delete one admin-owned patient and all dependent persisted session data.

        All SQL, including LangGraph checkpoints stored in this PostgreSQL database,
        participates in the caller's db_session_scope transaction.
        """
        patient_code = str(patient_code or "").strip()
        if not patient_code or patient_code.startswith("__draft__:"):
            raise ValueError("Patient record was not found.")

        scope = {"admin_id": admin_id, "patient_code": patient_code}
        patients = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM patients
                    WHERE admin_id = :admin_id AND patient_code = :patient_code
                    FOR UPDATE
                    """
                ),
                scope,
            )
            .mappings()
            .all()
        )
        patient_ids = [row["id"] for row in patients]

        sessions = (
            self.db.execute(
                text(
                    """
                    SELECT ps.id
                    FROM patient_sessions ps
                    WHERE ps.admin_id = :admin_id
                      AND (
                        ps.patient_id IN (
                            SELECT p.id FROM patients p
                            WHERE p.admin_id = :admin_id AND p.patient_code = :patient_code
                        )
                        OR ps.draft_profile #>> '{fields,patientId}' = :patient_code
                      )
                    FOR UPDATE
                    """
                ),
                scope,
            )
            .mappings()
            .all()
        )
        session_ids = [str(row["id"]) for row in sessions]

        report = (
            self.db.execute(
                text(
                    """
                    SELECT id
                    FROM patient_reports
                    WHERE admin_id = :admin_id
                      AND (
                        patient_code = :patient_code
                        OR patient_id IN (
                            SELECT p.id FROM patients p
                            WHERE p.admin_id = :admin_id AND p.patient_code = :patient_code
                        )
                        OR session_id::text IN (
                            SELECT ps.id::text FROM patient_sessions ps
                            WHERE ps.admin_id = :admin_id
                              AND (
                                ps.patient_id IN (
                                    SELECT p.id FROM patients p
                                    WHERE p.admin_id = :admin_id AND p.patient_code = :patient_code
                                )
                                OR ps.draft_profile #>> '{fields,patientId}' = :patient_code
                              )
                        )
                      )
                    FOR UPDATE
                    """
                ),
                scope,
            )
            .mappings()
            .all()
        )

        if not patient_ids and not session_ids and not report:
            raise ValueError("Patient record was not found.")

        if session_ids:
            for session_id in sorted(session_ids):
                acquire_session_activity_lock(self.db, session_id)

            for table_name in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                table_exists = self.db.execute(
                    text("SELECT to_regclass(:relation_name)"),
                    {"relation_name": f"public.{table_name}"},
                ).scalar()
                if table_exists:
                    statement = text(
                        f"DELETE FROM public.{table_name} "
                        "WHERE thread_id::text IN :session_ids"
                    ).bindparams(bindparam("session_ids", expanding=True))
                    self.db.execute(statement, {"session_ids": session_ids})

            self.db.execute(
                text(
                    """
                    DELETE FROM quiz_answers
                    WHERE quiz_attempt_id IN (
                        SELECT id FROM quiz_attempts WHERE session_id::text IN :session_ids
                    )
                    """
                ).bindparams(bindparam("session_ids", expanding=True)),
                {"session_ids": session_ids},
            )
            self.db.execute(
                text(
                    """
                    DELETE FROM quiz_attempts
                    WHERE session_id::text IN :session_ids
                    """
                ).bindparams(bindparam("session_ids", expanding=True)),
                {"session_ids": session_ids},
            )

        self.db.execute(
            text(
                """
                DELETE FROM patient_reports
                WHERE admin_id = :admin_id
                  AND (
                    patient_code = :patient_code
                    OR patient_id IN (
                        SELECT p.id FROM patients p
                        WHERE p.admin_id = :admin_id AND p.patient_code = :patient_code
                    )
                    OR session_id::text IN (
                        SELECT ps.id::text FROM patient_sessions ps
                        WHERE ps.admin_id = :admin_id
                          AND (
                            ps.patient_id IN (
                                SELECT p.id FROM patients p
                                WHERE p.admin_id = :admin_id AND p.patient_code = :patient_code
                            )
                            OR ps.draft_profile #>> '{fields,patientId}' = :patient_code
                          )
                    )
                  )
                """
            ),
            scope,
        )
        self.db.execute(
            text(
                """
                DELETE FROM patient_sessions
                WHERE admin_id = :admin_id
                  AND (
                    patient_id IN (
                        SELECT p.id FROM patients p
                        WHERE p.admin_id = :admin_id AND p.patient_code = :patient_code
                    )
                    OR draft_profile #>> '{fields,patientId}' = :patient_code
                  )
                """
            ),
            scope,
        )
        self.db.execute(
            text(
                """
                DELETE FROM patients
                WHERE admin_id = :admin_id AND patient_code = :patient_code
                """
            ),
            scope,
        )

        return {
            "patient_code": patient_code,
            "patient_ids": patient_ids,
            "session_ids": session_ids,
            "deleted_report_count": len(report),
        }

    def fetch_single_report(self, report_id: str, admin_id: int) -> AdminReportDetail:
        try:
            report_primary_id = int(report_id)
        except ValueError as exc:
            raise ValueError(f"Report {report_id} was not found.") from exc

        report = (
            self.db.execute(
                text(
                    """
                    SELECT
                        pr.id,
                        pr.admin_id,
                        pr.patient_id,
                        pr.session_id,
                        pr.patient_code,
                        pr.age,
                        pr.gender,
                        pr.educational_qualification,
                        pr.occupation,
                        pr.diet_type,
                        pr.alcohol_habit,
                        pr.smoking_habit,
                        pr.language,
                        pr.cld_status,
                        pr.exercise_habit,
                        pr.symptoms,
                        pr.session_started_at,
                        pr.session_ended_at,
                        pr.session_duration_minutes,
                        pr.pre_score,
                        pr.post_score,
                        pr.improvement,
                        pr.pre_score_level,
                        pr.post_score_level,
                        pr.weak_topics,
                        pr.learning_summary,
                        pr.completion_status,
                        pr.pdf_path,
                        pr.created_at,
                        pr.updated_at,
                        ps.status AS session_status,
                        ps.selected_language,
                        ps.draft_profile,
                        ps.started_at,
                        ps.ended_at
                    FROM patient_reports pr
                    LEFT JOIN patient_sessions ps ON ps.id = pr.session_id
                    WHERE pr.id = :report_id AND pr.admin_id = :admin_id
                    LIMIT 1
                    """
                ),
                {"report_id": report_primary_id, "admin_id": admin_id},
            )
            .mappings()
            .first()
        )
        if report is None:
            raise ValueError(f"Report {report_id} was not found.")

        attempts = (
            self.db.execute(
                text(
                    """
                    SELECT
                        id,
                        session_id,
                        quiz_type,
                        total_questions,
                        correct_answers,
                        score,
                        score_level,
                        weak_topics,
                        created_at
                    FROM quiz_attempts
                    WHERE session_id = CAST(:session_id AS uuid)
                    ORDER BY created_at ASC, id ASC
                    """
                ),
                {"session_id": str(report["session_id"])},
            )
            .mappings()
            .all()
        )
        answers_by_attempt_id: dict[int, list[dict]] = {}
        attempt_ids = [attempt["id"] for attempt in attempts]
        if attempt_ids:
            answer_rows = (
                self.db.execute(
                    text(
                        """
                        SELECT
                            quiz_attempt_id,
                            question_number,
                            question_text,
                            selected_answer,
                            correct_answer,
                            is_correct,
                            topic,
                            explanation,
                            created_at
                        FROM quiz_answers
                        WHERE quiz_attempt_id = ANY(:attempt_ids)
                        ORDER BY question_number ASC, id ASC
                        """
                    ),
                    {"attempt_ids": attempt_ids},
                )
                .mappings()
                .all()
            )
            for answer in answer_rows:
                answers_by_attempt_id.setdefault(answer["quiz_attempt_id"], []).append(dict(answer))

        attempt_by_type = {attempt["quiz_type"]: dict(attempt) for attempt in attempts}
        draft = report.get("draft_profile")
        if isinstance(draft, str):
            try:
                draft = json.loads(draft)
            except (TypeError, ValueError):
                draft = None
        draft_fields = draft.get("fields", draft) if isinstance(draft, dict) else {}
        draft_fields = draft_fields if isinstance(draft_fields, dict) else {}

        patient_detail = {
            "patient_id": report["patient_code"],
            "patient_code": report["patient_code"],
            "patient_db_id": report["patient_id"],
            "age": report["age"],
            "gender": report["gender"],
            "educational_qualification": report["educational_qualification"],
            "occupation": report["occupation"],
            "diet_type": report["diet_type"],
            "alcohol_habit": report["alcohol_habit"],
            "smoking_habit": report["smoking_habit"],
            "language": report["language"],
            "selected_language": report["selected_language"] or report["language"],
            "cld_status": report["cld_status"],
            "exercise_habit": report["exercise_habit"],
            "symptoms": report["symptoms"] or [],
        }
        patient_detail.update({
            key: draft_fields.get(key)
            for key in (
                "ageGroup", "maritalStatus", "familyType", "residence", "religion",
                "socioeconomicStatus", "cldDuration", "cldEtiology", "cldEtiologyOther",
                "cldStage", "cldStageOther", "comorbidities", "comorbiditiesOther",
                "sarcopeniaDuration", "cldTreatment", "cldTreatmentOther",
                "hospitalizationHistory", "nutritionalCounselling", "previousHealthEducation",
                "habits", "appetiteLevel", "proteinAwareness", "exerciseType",
                "exerciseFrequency", "weaknessFatigue", "recentWeightLoss", "digitalLiteracy",
            )
        })
        if patient_detail.get("habits") in (None, ""):
            legacy_habits = []
            if str(report.get("alcohol_habit") or "").strip().lower() in {"yes", "true", "1"}:
                legacy_habits.append("alcohol")
            if str(report.get("smoking_habit") or "").strip().lower() in {"yes", "true", "1"}:
                legacy_habits.append("smoking")
            if legacy_habits:
                patient_detail["habits"] = legacy_habits
            elif report.get("alcohol_habit") is not None and report.get("smoking_habit") is not None:
                patient_detail["habits"] = ["none"]

        return AdminReportDetail(
            report_id=str(report["id"]),
            session_id=str(report["session_id"]),
            patient=patient_detail,
            session={
                "session_id": str(report["session_id"]),
                "session_start_time": report["session_started_at"] or report["started_at"],
                "session_end_time": report["session_ended_at"] or report["ended_at"],
                "session_duration_minutes": report["session_duration_minutes"],
                "completion_status": report["completion_status"],
                "status": report["session_status"] or report["completion_status"],
                "learning_summary": report["learning_summary"],
            },
            report={
                "pre_test_score": report["pre_score"],
                "post_test_score": report["post_score"],
                "improvement": report["improvement"],
                "score_level": report["post_score_level"] or report["pre_score_level"],
                "pre_score_level": report["pre_score_level"],
                "post_score_level": report["post_score_level"],
                "weak_topics": report["weak_topics"] or [],
                "strong_topics": [],
                "learning_summary": report["learning_summary"],
                "completion_status": report["completion_status"],
                "pdf_path": report["pdf_path"],
                "report_generated_at": report["updated_at"] or report["created_at"],
            },
            pre_test=self._mapping_attempt_to_schema(
                attempt_by_type.get("pre"),
                answers_by_attempt_id.get(attempt_by_type.get("pre", {}).get("id"), []),
            ),
            post_test=self._mapping_attempt_to_schema(
                attempt_by_type.get("post"),
                answers_by_attempt_id.get(attempt_by_type.get("post", {}).get("id"), []),
            ),
        )
