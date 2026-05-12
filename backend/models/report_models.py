from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from database import Base


class HospitalAdmin(Base):
    __tablename__ = "hospital_admin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    username: Mapped[str] = mapped_column(Text, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("hospital_admin.id"), index=True)
    patient_id: Mapped[str] = mapped_column("patient_code", Text, index=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)
    educational_qualification: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(Text, nullable=True)
    diet_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    alcohol_habit: Mapped[str | None] = mapped_column(Text, nullable=True)
    smoking_habit: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    cld_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    exercise_habit: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["SessionRecord"]] = relationship(back_populates="patient")


class SessionRecord(Base):
    __tablename__ = "patient_sessions"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("hospital_admin.id"), index=True)
    patient_id_fk: Mapped[int] = mapped_column("patient_id", ForeignKey("patients.id"), index=True)
    completion_status: Mapped[str | None] = mapped_column("status", Text, nullable=True)
    selected_language: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_chat_summary: Mapped[str | None] = mapped_column("chat_summary", Text, nullable=True)
    learning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    weak_topics: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    session_start_time: Mapped[datetime | None] = mapped_column("started_at", DateTime(timezone=True), nullable=True)
    session_end_time: Mapped[datetime | None] = mapped_column("ended_at", DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped[Patient] = relationship(back_populates="sessions")
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(back_populates="session")
    report: Mapped["SessionReport | None"] = relationship(back_populates="session", uselist=False)

    @property
    def session_id(self) -> str:
        return self.id


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_fk: Mapped[str] = mapped_column("session_id", ForeignKey("patient_sessions.id"), index=True)
    quiz_type: Mapped[str] = mapped_column(Text, index=True)
    total_questions: Mapped[int] = mapped_column(Integer)
    correct_answers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score: Mapped[int] = mapped_column(Integer)
    score_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    weak_topics: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[SessionRecord] = relationship(back_populates="quiz_attempts")
    answers: Mapped[list["QuizAnswer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")

    @property
    def submitted_at(self) -> datetime | None:
        return self.created_at

    @property
    def strong_topics(self) -> list[str]:
        return []


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_fk: Mapped[int] = mapped_column("quiz_attempt_id", ForeignKey("quiz_attempts.id"), index=True)
    question_id: Mapped[int] = mapped_column("question_number", Integer)
    question_text: Mapped[str] = mapped_column(Text)
    selected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt: Mapped[QuizAttempt] = relationship(back_populates="answers")


class SessionReport(Base):
    __tablename__ = "patient_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("hospital_admin.id"), index=True)
    patient_db_id: Mapped[int | None] = mapped_column("patient_id", ForeignKey("patients.id"), nullable=True)
    session_fk: Mapped[str] = mapped_column("session_id", ForeignKey("patient_sessions.id"), unique=True, index=True)
    patient_id_text: Mapped[str | None] = mapped_column("patient_code", Text, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)
    educational_qualification: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(Text, nullable=True)
    diet_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    alcohol_habit: Mapped[str | None] = mapped_column(Text, nullable=True)
    smoking_habit: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    cld_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    exercise_habit: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    session_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    session_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pre_test_score: Mapped[int | None] = mapped_column("pre_score", Integer, nullable=True)
    post_test_score: Mapped[int | None] = mapped_column("post_score", Integer, nullable=True)
    improvement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pre_score_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_score_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    weak_topics: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    short_chat_summary: Mapped[str | None] = mapped_column("chat_summary", Text, nullable=True)
    learning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    completion_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[SessionRecord] = relationship(back_populates="report")

    @property
    def report_generated_at(self) -> datetime | None:
        return self.updated_at or self.created_at


class LearningMedia(Base):
    __tablename__ = "learning_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(Text, index=True)
    media_type: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    bucket_name: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
