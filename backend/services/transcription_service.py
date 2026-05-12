from __future__ import annotations

from pathlib import Path
from typing import Any

from services.gemini_service import GeminiService


class VoiceTranscriptionService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service

    def transcribe(
        self,
        *,
        file_path: Path,
        mime_type: str,
        preferred_language: str | None = None,
    ) -> dict[str, Any]:
        return self.gemini_service.transcribe_audio(
            file_path=file_path,
            mime_type=mime_type,
            preferred_language=preferred_language,
        )
