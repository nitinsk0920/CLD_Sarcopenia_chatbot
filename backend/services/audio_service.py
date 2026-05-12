from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from config import Settings
from services.gemini_service import GeminiService
from services.language_utils import normalize_language_code


@dataclass(slots=True)
class AudioCacheRecord:
    session_id: str
    audio_id: str
    file_path: Path
    cached: bool


class SessionAudioService:
    def __init__(self, settings: Settings, gemini_service: GeminiService):
        self.settings = settings
        self.gemini_service = gemini_service
        self.settings.audio_cache_dir.mkdir(parents=True, exist_ok=True)

    def _session_dir(self, session_id: str) -> Path:
        safe_session = "".join(ch for ch in session_id if ch.isalnum() or ch in {"-", "_"})
        return self.settings.audio_cache_dir / (safe_session or "anonymous")

    def get_or_create_audio(
        self,
        *,
        session_id: str,
        response_text: str,
        language_code: str,
    ) -> AudioCacheRecord:
        session_dir = self._session_dir(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(
            f"{normalize_language_code(language_code)}::{response_text.strip()}".encode("utf-8")
        ).hexdigest()[:24]
        audio_id = f"{digest}.wav"
        target = session_dir / audio_id
        if target.exists():
            return AudioCacheRecord(
                session_id=session_id,
                audio_id=audio_id,
                file_path=target,
                cached=True,
            )

        self.gemini_service.synthesize_speech(
            text=response_text,
            language_code=language_code,
            destination=target,
        )
        return AudioCacheRecord(
            session_id=session_id,
            audio_id=audio_id,
            file_path=target,
            cached=False,
        )

    def resolve_audio_path(self, session_id: str, audio_id: str) -> Path:
        return self._session_dir(session_id) / audio_id

    def clear_session_cache(self, session_id: str) -> None:
        session_dir = self._session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)
