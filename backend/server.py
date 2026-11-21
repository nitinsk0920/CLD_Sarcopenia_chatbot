from __future__ import annotations

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from chatbot_graph import HealthcareEducationChatbot
from auth.subscription import get_current_active_admin
from config import get_settings
from db.database import get_db
from database import initialize_database
from routes.auth_routes import router as auth_router
from routes.learning_routes import router as learning_router
from routes.report_routes import router as report_router
from routes.subscription_routes import router as subscription_router
from services.audio_service import SessionAudioService
from services.checkpointer import create_checkpointer
from services.gemini_service import GeminiService
from services.language_utils import normalize_language_code
from services.rag_service import FaissKnowledgeService
from services.transcription_service import VoiceTranscriptionService
from loadtest.config import loadtest_request_requires_mock_rejection


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    question: str = Field(default="")
    selected_language: str = Field(default="en")
    transcribed_language: str = Field(default="")
    patient_context: dict[str, Any] = Field(default_factory=dict)
    weak_topic_summary: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id: str
    answer_id: str
    answer: str
    selected_topics: list[str]
    response_language: str
    faq_first_match: dict[str, Any] | None = None
    retrieved_chunks: list[dict[str, Any]]
    safety: dict[str, Any]
    session_summary: str = ""


class ChatHistoryResponse(BaseModel):
    session_id: str
    session_summary: str = ""
    messages: list[dict[str, str]] = Field(default_factory=list)


class AudioRequest(BaseModel):
    session_id: str = Field(min_length=1)
    answer_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    language: str = Field(default="en")


class AudioResponse(BaseModel):
    session_id: str
    answer_id: str
    audio_id: str
    audio_url: str
    cached: bool


class TranscriptionResponse(BaseModel):
    session_id: str
    transcript: str
    detected_language: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    from concurrent.futures import ThreadPoolExecutor

    settings = get_settings()
    from loadtest.config import loadtest_mock_mode_enabled
    from rag_retriever import initialize_loadtest_mock_vector_resources
    from rag_retriever import initialize_vector_resources

    mock_mode = loadtest_mock_mode_enabled()
    if mock_mode:
        initialize_loadtest_mock_vector_resources()
        logging.getLogger(__name__).warning(
            "LOADTEST MOCK MODE ENABLED: generation=LocalMockGeneration, "
            "embeddings=DeterministicLocalHash, TTS=SilentWav, "
            "STT=FixedSyntheticTranscript; external Gemini provider access is blocked."
        )
    else:
        initialize_vector_resources()
    gemini_service = GeminiService(settings, loadtest_mock=mock_mode)
    checkpointer_resources = create_checkpointer(settings)
    if checkpointer_resources.backend_name == "postgres":
        logging.getLogger(__name__).info("LangGraph conversation persistence is using PostgreSQL.")
    else:
        logging.getLogger(__name__).warning(
            "LangGraph conversation persistence is in-memory; configure LANGGRAPH_POSTGRES_URL "
            "or DATABASE_URL to retain sessions across backend restarts."
        )
    rag_service = FaissKnowledgeService()
    audio_service = SessionAudioService(settings, gemini_service)
    transcription_service = VoiceTranscriptionService(gemini_service)
    chatbot = HealthcareEducationChatbot(
        rag_service=rag_service,
        gemini_service=gemini_service,
        checkpointer=checkpointer_resources.saver,
    )
    if mock_mode and chatbot.gemini_service is not gemini_service:
        raise RuntimeError("Load-test mock generation provider was not injected into the chatbot graph.")

    app.state.settings = settings
    app.state.gemini_service = gemini_service
    app.state.checkpointer_resources = checkpointer_resources
    app.state.audio_service = audio_service
    app.state.transcription_service = transcription_service
    app.state.chatbot = chatbot
    app.state.loadtest_mock_mode = mock_mode
    app.state.chat_executor = ThreadPoolExecutor(max_workers=4)
    app.state.reporting_enabled = initialize_database()

    try:
        yield
    finally:
        app.state.chat_executor.shutdown(wait=False, cancel_futures=True)
        gemini_service.close()
        checkpointer_resources.close()


app = FastAPI(
    title="CLD Sarcopenia Education Chatbot API",
    version="0.2.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def require_loadtest_mocks_for_locust(request, call_next):
    """A Locust-only precondition header can reject unsafe runs, never enable mocks."""
    if loadtest_request_requires_mock_rejection(
        request.headers.get("x-require-loadtest-mocks", ""),
        getattr(app.state, "loadtest_mock_mode", False),
    ):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Locust requires local mock providers; backend mock mode is not active."
            },
        )
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(learning_router)
app.include_router(report_router)
app.include_router(subscription_router)


def _mask_session_id(session_id: str) -> str:
    cleaned = str(session_id or "")
    return f"{cleaned[:4]}…{cleaned[-4:]}" if len(cleaned) > 8 else "[masked]"


def _safe_error_detail(exc: Exception) -> str:
    detail = str(exc).replace("\n", " ").strip()
    detail = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_KEY]", detail)
    detail = re.sub(r"(?i)Bearer\s+\S+", "Bearer [REDACTED]", detail)
    detail = re.sub(r"(?i)(postgres(?:ql)?://)[^\s@]+@", r"\1[REDACTED]@", detail)
    return detail[:300] or type(exc).__name__


def _run_chat_sync(
    app: FastAPI,
    payload: ChatRequest,
    verified_profile: dict[str, Any],
    request_id: str,
) -> dict[str, Any]:
    chatbot: HealthcareEducationChatbot = app.state.chatbot
    return chatbot.chat(
        session_id=payload.session_id,
        user_question=payload.question,
        patient_context=verified_profile,
        weak_topic_summary=payload.weak_topic_summary,
        selected_language=payload.selected_language,
        transcribed_language=payload.transcribed_language,
        request_id=request_id,
    )


def _require_active_session(session_id: str, admin_id: int, db: Session) -> dict[str, Any]:
    from services.report_service import ReportService

    profile = ReportService(db).get_active_session_profile(session_id, admin_id=admin_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Active patient session was not found.")
    return profile


@app.get("/health")
def health(db: Session = Depends(get_db)) -> str:
    db.execute(text("SELECT 1"))
    return "DB connected"


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> ChatResponse:
    from services.report_service import ReportService

    request_id = str(uuid4())
    masked_session = _mask_session_id(payload.session_id)
    stage = "profile_retrieval"
    logger = logging.getLogger(__name__)
    logger.info(
        "chat_request_started request_id=%s session=%s admin_id=%s selected_language=%s",
        request_id,
        masked_session,
        current_admin.id,
        payload.selected_language,
    )
    try:
        verified_profile = ReportService(db).get_active_session_profile(
            payload.session_id, admin_id=current_admin.id
        )
        if verified_profile is None:
            logger.warning(
                "chat_request_rejected request_id=%s session=%s stage=%s reason=inactive_or_unowned_session",
                request_id,
                masked_session,
                stage,
            )
            raise HTTPException(status_code=404, detail="Active patient session was not found.")

        stage = "langgraph_execution"
        loop = asyncio.get_running_loop()
        executor = app.state.chat_executor
        result = await asyncio.wait_for(
            loop.run_in_executor(
                executor, _run_chat_sync, app, payload, verified_profile, request_id
            ),
            timeout=get_settings().chat_timeout_seconds,
        )
        stage = "response_serialization"
        response = ChatResponse(**result)
        logger.info(
            "chat_request_completed request_id=%s session=%s language=%s chunks=%s "
            "response_chars=%s fallback=%s validation_reason=%s",
            request_id,
            masked_session,
            response.response_language,
            len(response.retrieved_chunks),
            len(response.answer),
            bool(response.safety.get("flagged")),
            response.safety.get("reason", "none"),
        )
        return response
    except asyncio.TimeoutError as exc:
        logger.error(
            "chat_request_failed request_id=%s session=%s stage=%s exception=%s detail=request_timeout",
            request_id,
            masked_session,
            stage,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=504,
            detail="Chatbot timed out. Please retry your question.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "chat_request_failed request_id=%s session=%s stage=%s exception=%s detail=%s",
            request_id,
            masked_session,
            stage,
            type(exc).__name__,
            _safe_error_detail(exc),
        )
        raise HTTPException(status_code=500, detail=f"Chatbot pipeline error: {exc}") from exc


@app.get("/api/chat/session/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    _require_active_session(session_id, current_admin.id, db)
    chatbot: HealthcareEducationChatbot = app.state.chatbot
    history = await asyncio.to_thread(chatbot.get_conversation_history, session_id)
    return ChatHistoryResponse(session_id=session_id, **history)


@app.post("/api/chat/audio", response_model=AudioResponse)
async def create_audio(
    payload: AudioRequest,
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> AudioResponse:
    _require_active_session(payload.session_id, current_admin.id, db)
    audio_service: SessionAudioService = app.state.audio_service
    try:
        record = await asyncio.to_thread(
            audio_service.get_or_create_audio,
            session_id=payload.session_id,
            response_text=payload.text,
            language_code=normalize_language_code(payload.language),
        )
        return AudioResponse(
            session_id=payload.session_id,
            answer_id=payload.answer_id,
            audio_id=record.audio_id,
            audio_url=f"/api/chat/audio/{payload.session_id}/{record.audio_id}",
            cached=record.cached,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {exc}") from exc


@app.get("/api/chat/audio/{session_id}/{audio_id}")
async def get_audio(
    session_id: str,
    audio_id: str,
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> FileResponse:
    _require_active_session(session_id, current_admin.id, db)
    audio_service: SessionAudioService = app.state.audio_service
    path = audio_service.resolve_audio_path(session_id, audio_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(path, media_type="audio/wav", filename=audio_id)


@app.delete("/api/chat/session/{session_id}/audio")
async def clear_session_audio(
    session_id: str,
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    _require_active_session(session_id, current_admin.id, db)
    audio_service: SessionAudioService = app.state.audio_service
    audio_service.clear_session_cache(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.delete("/api/chat/session/{session_id}")
async def clear_chat_session(
    session_id: str,
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    from services.report_service import ReportService

    discarded = ReportService(db).discard_draft_session(session_id, admin_id=current_admin.id)
    if not discarded:
        raise HTTPException(status_code=404, detail="Active patient session was not found.")
    resources = app.state.checkpointer_resources
    delete_thread = getattr(resources.saver, "delete_thread", None)
    if callable(delete_thread):
        await asyncio.to_thread(delete_thread, session_id)
    app.state.audio_service.clear_session_cache(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.post("/api/chat/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    session_id: str = Form(...),
    selected_language: str = Form("en"),
    audio_file: UploadFile = File(...),
    current_admin: Any = Depends(get_current_active_admin),
    db: Session = Depends(get_db),
) -> TranscriptionResponse:
    _require_active_session(session_id, current_admin.id, db)
    transcription_service: VoiceTranscriptionService = app.state.transcription_service
    suffix = Path(audio_file.filename or "voice-input.webm").suffix or ".webm"
    mime_type = audio_file.content_type or "audio/webm"

    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(await audio_file.read())

        result = await asyncio.to_thread(
            transcription_service.transcribe,
            file_path=temp_path,
            mime_type=mime_type,
            preferred_language=normalize_language_code(selected_language),
        )
        return TranscriptionResponse(
            session_id=session_id,
            transcript=result["transcript"],
            detected_language=normalize_language_code(result.get("language_code")),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {exc}") from exc
    finally:
        try:
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass
