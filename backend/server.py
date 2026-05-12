from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import FastAPI
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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
    gemini_service = GeminiService(settings)
    checkpointer_resources = create_checkpointer(settings)
    rag_service = FaissKnowledgeService()
    audio_service = SessionAudioService(settings, gemini_service)
    transcription_service = VoiceTranscriptionService(gemini_service)
    chatbot = HealthcareEducationChatbot(
        rag_service=rag_service,
        gemini_service=gemini_service,
        checkpointer=checkpointer_resources.saver,
    )

    app.state.settings = settings
    app.state.gemini_service = gemini_service
    app.state.checkpointer_resources = checkpointer_resources
    app.state.audio_service = audio_service
    app.state.transcription_service = transcription_service
    app.state.chatbot = chatbot
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


def _run_chat_sync(app: FastAPI, payload: ChatRequest) -> dict[str, Any]:
    chatbot: HealthcareEducationChatbot = app.state.chatbot
    return chatbot.chat(
        session_id=payload.session_id,
        user_question=payload.question,
        patient_context=payload.patient_context,
        weak_topic_summary=payload.weak_topic_summary,
        selected_language=payload.selected_language,
        transcribed_language=payload.transcribed_language,
    )


@app.get("/health")
def health(db: Session = Depends(get_db)) -> str:
    db.execute(text("SELECT 1"))
    return "DB connected"


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_admin: Any = Depends(get_current_active_admin),
) -> ChatResponse:
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    loop = asyncio.get_running_loop()
    executor = app.state.chat_executor
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, _run_chat_sync, app, payload),
            timeout=get_settings().chat_timeout_seconds,
        )
        return ChatResponse(**result)
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Chatbot timed out. Please retry your question.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Chatbot pipeline error: {exc}") from exc


@app.post("/api/chat/audio", response_model=AudioResponse)
async def create_audio(
    payload: AudioRequest,
    current_admin: Any = Depends(get_current_active_admin),
) -> AudioResponse:
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
) -> FileResponse:
    audio_service: SessionAudioService = app.state.audio_service
    path = audio_service.resolve_audio_path(session_id, audio_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(path, media_type="audio/wav", filename=audio_id)


@app.delete("/api/chat/session/{session_id}/audio")
async def clear_session_audio(
    session_id: str,
    current_admin: Any = Depends(get_current_active_admin),
) -> dict[str, str]:
    audio_service: SessionAudioService = app.state.audio_service
    audio_service.clear_session_cache(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.post("/api/chat/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    session_id: str = Form(...),
    selected_language: str = Form("en"),
    audio_file: UploadFile = File(...),
    current_admin: Any = Depends(get_current_active_admin),
) -> TranscriptionResponse:
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
