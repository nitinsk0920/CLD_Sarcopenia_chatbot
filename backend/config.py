from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE_PATHS = (BASE_DIR / ".env", BASE_DIR / ".env.example")


def _strip_wrapping_quotes(value: str) -> str:
    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        return cleaned[1:-1]
    return cleaned


def load_local_env_files() -> None:
    for env_path in ENV_FILE_PATHS:
        if not env_path.exists():
            continue

        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            env_key = key.strip()
            if not env_key or env_key in os.environ:
                continue

            os.environ[env_key] = _strip_wrapping_quotes(value)

        # Prefer the first matching env file, usually `.env`.
        break


load_local_env_files()


@dataclass(slots=True)
class Settings:
    gemini_model_primary: str
    gemini_model_fallback_1: str
    gemini_model_fallback_2: str
    gemini_tts_model_primary: str
    gemini_tts_model_fallback_1: str
    model_max_retry: int
    model_timeout_ms: int
    gemini_model: str
    gemini_tts_model: str
    gemini_api_key: str
    chat_timeout_seconds: int
    audio_cache_dir: Path
    report_pdf_dir: Path
    database_url: str
    postgres_url: str
    allow_in_memory_fallback: bool
    default_voice_name: str
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_access_token_expire_minutes: int
    supabase_url: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    gemini_model_primary = (
        os.getenv("GEMINI_MODEL_PRIMARY", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")).strip()
        or "gemini-2.5-flash"
    )
    gemini_model_fallback_1 = (
        os.getenv("GEMINI_MODEL_FALLBACK_1", "gemini-2.0-flash").strip() or "gemini-2.0-flash"
    )
    gemini_model_fallback_2 = (
        os.getenv("GEMINI_MODEL_FALLBACK_2", "gemini-1.5-flash").strip() or "gemini-1.5-flash"
    )
    gemini_tts_model_primary = (
        os.getenv(
            "GEMINI_TTS_MODEL_PRIMARY",
            os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts"),
        ).strip()
        or "gemini-2.5-flash-preview-tts"
    )
    gemini_tts_model_fallback_1 = (
        os.getenv("GEMINI_TTS_MODEL_FALLBACK_1", "gemini-2.0-flash-exp").strip()
        or "gemini-2.0-flash-exp"
    )
    return Settings(
        gemini_model_primary=gemini_model_primary,
        gemini_model_fallback_1=gemini_model_fallback_1,
        gemini_model_fallback_2=gemini_model_fallback_2,
        gemini_tts_model_primary=gemini_tts_model_primary,
        gemini_tts_model_fallback_1=gemini_tts_model_fallback_1,
        model_max_retry=int(os.getenv("MODEL_MAX_RETRY", "1")),
        model_timeout_ms=int(os.getenv("MODEL_TIMEOUT_MS", "25000")),
        gemini_model=gemini_model_primary,
        gemini_tts_model=gemini_tts_model_primary,
        gemini_api_key=os.getenv("GOOGLE_API_KEY", os.getenv("GEMINI_API_KEY", "")).strip(),
        chat_timeout_seconds=int(os.getenv("CHAT_TIMEOUT_SECONDS", "60")),
        audio_cache_dir=Path(
            os.getenv(
                "AUDIO_CACHE_DIR",
                str(BASE_DIR / "runtime" / "session_audio"),
            )
        ).resolve(),
        report_pdf_dir=Path(
            os.getenv(
                "REPORT_PDF_DIR",
                str(BASE_DIR / "runtime" / "report_pdfs"),
            )
        ).resolve(),
        database_url=os.getenv("DATABASE_URL", os.getenv("SUPABASE_DATABASE_URL", "")).strip(),
        postgres_url=os.getenv("LANGGRAPH_POSTGRES_URL", os.getenv("DATABASE_URL", "")).strip(),
        allow_in_memory_fallback=os.getenv("ALLOW_IN_MEMORY_CHECKPOINTER_FALLBACK", "true").lower()
        != "false",
        default_voice_name=os.getenv("GEMINI_TTS_VOICE", "Kore").strip() or "Kore",
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", os.getenv("JWT_SECRET", "")).strip(),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256",
        jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480")),
        supabase_url=os.getenv("SUPABASE_URL", "").strip(),
    )
