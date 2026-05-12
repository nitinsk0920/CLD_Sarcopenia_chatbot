from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class PatientProfilePayload(BaseModel):
    patientId: str
    age: int | None = None
    gender: str | None = None
    educationalQualification: str | None = None
    occupation: str | None = None
    dietType: str | None = None
    habits: list[str] = Field(default_factory=list)
    languagePreference: str | None = None
    digitalLiteracy: str | None = None
    cldStatus: str | None = None
    illnessDuration: str | None = None
    weaknessFatigue: str | None = None
    recentWeightLoss: str | None = None
    appetiteLevel: str | None = None
    exerciseRegular: str | None = None
    exerciseType: str | None = None
    exerciseFrequency: str | None = None
    symptoms: list[str] = Field(default_factory=list)


class SessionStartRequest(BaseModel):
    session_id: str
    started_at: datetime | None = None
    patient: PatientProfilePayload


class SessionEndRequest(BaseModel):
    session_id: str
    ended_at: datetime | None = None
    completion_status: str = "completed"


class QuizAnswerPayload(BaseModel):
    question_id: int
    question_text: str
    topic: str
    selected_index: int | None = None
    selected_answer: str | None = None
    correct_index: int | None = None
    correct_answer: str | None = None
    is_correct: bool
    explanation: str | None = None


class QuizAttemptPayload(BaseModel):
    quiz_type: str
    score: int
    total_questions: int
    score_level: str | None = None
    weak_topics: list[str] = Field(default_factory=list)
    strong_topics: list[str] = Field(default_factory=list)
    submitted_at: datetime | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    answers: list[QuizAnswerPayload] = Field(default_factory=list)


class FinalReportSaveRequest(BaseModel):
    session_id: str
    session_started_at: datetime | None = None
    session_ended_at: datetime | None = None
    patient: PatientProfilePayload
    pre_test: QuizAttemptPayload
    post_test: QuizAttemptPayload
    short_chat_summary: str = ""
    learning_summary: str = ""
    completion_status: str = "completed"
    doctor_note: str | None = None


class SessionStartResponse(BaseModel):
    session_id: str
    patient_id: str
    status: str


class SessionEndResponse(BaseModel):
    session_id: str
    status: str


class ReportSaveResponse(BaseModel):
    report_id: str
    session_id: str
    status: str


class AdminReportListItem(BaseModel):
    report_id: str
    session_id: str
    patient_id: str
    patient_code: str | None = None
    age: int | None = None
    gender: str | None = None
    language: str | None = None
    pre_test_score: int | None = None
    post_test_score: int | None = None
    score: int | None = None
    improvement: int | None = None
    weak_topics: list[str] = Field(default_factory=list)
    completion_status: str
    session_start_time: datetime | None = None
    session_end_time: datetime | None = None
    report_date: datetime | None = None


class AdminQuizAnswerItem(BaseModel):
    question_id: int
    question_text: str
    topic: str
    selected_answer: str | None = None
    correct_answer: str | None = None
    is_correct: bool
    explanation: str | None = None


class AdminQuizAttemptDetail(BaseModel):
    quiz_type: str
    score: int
    total_questions: int
    score_level: str | None = None
    weak_topics: list[str] = Field(default_factory=list)
    strong_topics: list[str] = Field(default_factory=list)
    submitted_at: datetime | None = None
    answers: list[AdminQuizAnswerItem] = Field(default_factory=list)


class AdminReportDetail(BaseModel):
    report_id: str
    session_id: str
    patient: dict[str, Any]
    session: dict[str, Any]
    report: dict[str, Any]
    pre_test: AdminQuizAttemptDetail | None = None
    post_test: AdminQuizAttemptDetail | None = None
