from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from schemas.report_schemas import AdminQuizAttemptDetail
from schemas.report_schemas import AdminReportDetail
from schemas.report_schemas import AdminReportListItem
from schemas.report_schemas import FinalReportSaveRequest
from schemas.report_schemas import PatientProfilePayload
from schemas.report_schemas import QuizAttemptPayload


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _habit_text(enabled: bool) -> str:
        return "yes" if enabled else "no"

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
        chat_summary = payload.short_chat_summary.strip()

        existing = (
            self.db.execute(
                text(
                    """
                    SELECT id
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
            "chat_summary": chat_summary,
            "learning_summary": learning_summary,
            "weak_topics": weak_topics,
            "started_at": started_at,
            "ended_at": ended_at,
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
                        chat_summary,
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
                        :chat_summary,
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
                        admin_id = :admin_id,
                        patient_id = :patient_id,
                        status = :status,
                        selected_language = :selected_language,
                        chat_summary = :chat_summary,
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
            "chat_summary": payload.short_chat_summary.strip(),
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
                            chat_summary,
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
                            :chat_summary,
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
                    chat_summary = :chat_summary,
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
                        pr.chat_summary,
                        pr.learning_summary,
                        pr.completion_status,
                        pr.pdf_path,
                        pr.created_at,
                        pr.updated_at,
                        ps.status AS session_status,
                        ps.selected_language,
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
        return AdminReportDetail(
            report_id=str(report["id"]),
            session_id=str(report["session_id"]),
            patient={
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
            },
            session={
                "session_id": str(report["session_id"]),
                "session_start_time": report["session_started_at"] or report["started_at"],
                "session_end_time": report["session_ended_at"] or report["ended_at"],
                "session_duration_minutes": report["session_duration_minutes"],
                "completion_status": report["completion_status"],
                "status": report["session_status"] or report["completion_status"],
                "short_chat_summary": report["chat_summary"],
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
                "short_chat_summary": report["chat_summary"],
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
