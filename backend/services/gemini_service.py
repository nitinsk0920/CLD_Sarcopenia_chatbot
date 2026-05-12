from __future__ import annotations

import json
import logging
import os
import wave
from pathlib import Path
from typing import Any

from config import Settings
from services.language_utils import language_name

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


logger = logging.getLogger(__name__)


class GeminiService:
    SERVICE_UNAVAILABLE_MESSAGE = "Service temporarily unavailable. Please try again shortly."
    COMPLETE_RESPONSE_INSTRUCTION = (
        "Provide complete, patient-friendly responses in clear full sentences. "
        "Do not abruptly stop mid-response."
    )

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = None

    def _ensure_client(self):
        if genai is None or types is None:
            raise RuntimeError(
                "Missing Google Gen AI SDK. Install backend requirements before starting the server."
            )

        if not self._client:
            if not self.settings.gemini_api_key and not (
                os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            ):
                raise RuntimeError(
                    "Gemini API key is not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY."
                )
            self._client = genai.Client(
                api_key=self.settings.gemini_api_key or None,
                http_options=types.HttpOptions(
                    client_args={
                        "trust_env": False,
                    },
                    timeout=max(self.settings.model_timeout_ms, 1),
                ),
            )
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def _chat_models(self) -> list[str]:
        return self._dedupe_models(
            [
                self.settings.gemini_model_primary,
                self.settings.gemini_model_fallback_1,
                self.settings.gemini_model_fallback_2,
            ]
        )

    def _tts_stt_models(self) -> list[str]:
        return self._dedupe_models(
            [
                self.settings.gemini_tts_model_primary,
                self.settings.gemini_tts_model_fallback_1,
            ]
        )

    @staticmethod
    def _dedupe_models(models: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for model in models:
            cleaned = (model or "").strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            ordered.append(cleaned)
        return ordered

    def _max_retry_per_model(self) -> int:
        return max(0, min(self.settings.model_max_retry, 1))

    def _is_retryable_failure(self, exc: Exception) -> tuple[bool, str]:
        if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
            return True, exc.__class__.__name__

        status_code = getattr(exc, "status_code", None)
        if status_code in {408, 409, 425, 429, 500, 502, 503, 504}:
            return True, f"http {status_code}"

        message = str(exc).strip()
        lowered = message.lower()

        non_retryable_markers = (
            "api key",
            "unauthorized",
            "forbidden",
            "permission denied",
            "permission",
            "invalid argument",
            "malformed",
            "authentication",
            "credentials",
        )
        if any(marker in lowered for marker in non_retryable_markers):
            return False, message or exc.__class__.__name__

        retryable_markers = (
            "timeout",
            "timed out",
            "deadline exceeded",
            "connection reset",
            "connection aborted",
            "connection refused",
            "temporary failure",
            "temporarily unavailable",
            "service unavailable",
            "server busy",
            "overloaded",
            "resource exhausted",
            "rate limit",
            "too many requests",
            "429",
            "unavailable model",
            "model is not available",
            "model not found",
            "unsupported model",
            "network",
        )
        if any(marker in lowered for marker in retryable_markers):
            return True, message or exc.__class__.__name__

        return False, message or exc.__class__.__name__

    def _run_with_model_fallback(
        self,
        *,
        models: list[str],
        mode_label: str,
        operation_label: str,
        request_runner,
    ):
        if not models:
            raise RuntimeError("No Gemini models are configured.")

        client = self._ensure_client()
        last_exc: Exception | None = None
        retries_per_model = self._max_retry_per_model()

        for model_index, model_name in enumerate(models):
            for attempt in range(retries_per_model + 1):
                if attempt == 0:
                    logger.info("[Gemini] %s using model=%s", operation_label, model_name)
                else:
                    logger.warning(
                        "[Gemini] %s retry attempt %s on model=%s",
                        operation_label,
                        attempt,
                        model_name,
                    )

                try:
                    return request_runner(client, model_name)
                except Exception as exc:  # pragma: no cover - depends on external SDK/runtime.
                    last_exc = exc
                    retryable, reason = self._is_retryable_failure(exc)
                    if not retryable:
                        logger.exception(
                            "[Gemini] %s failed on model=%s with non-retryable error: %s",
                            operation_label,
                            model_name,
                            reason,
                        )
                        raise RuntimeError(self.SERVICE_UNAVAILABLE_MESSAGE) from exc

                    if attempt < retries_per_model:
                        logger.warning(
                            "[Gemini] %s temporary failure on model=%s (%s). Retrying once.",
                            operation_label,
                            model_name,
                            reason,
                        )
                        continue

                    next_model = models[model_index + 1] if model_index + 1 < len(models) else None
                    if next_model:
                        logger.warning(
                            "[Gemini] %s %s model failed (%s) -> switching to %s",
                            operation_label,
                            mode_label,
                            reason,
                            next_model,
                        )
                    else:
                        logger.error(
                            "[Gemini] %s exhausted %s models after failure on %s (%s)",
                            operation_label,
                            mode_label,
                            model_name,
                            reason,
                        )
                    break

        raise RuntimeError(self.SERVICE_UNAVAILABLE_MESSAGE) from last_exc

    def _run_chat_with_fallback(self, operation_label: str, request_runner):
        return self._run_with_model_fallback(
            models=self._chat_models(),
            mode_label="chat",
            operation_label=operation_label,
            request_runner=request_runner,
        )

    def _run_tts_stt_with_fallback(self, operation_label: str, request_runner):
        return self._run_with_model_fallback(
            models=self._tts_stt_models(),
            mode_label="tts/stt",
            operation_label=operation_label,
            request_runner=request_runner,
        )

    @staticmethod
    def _looks_incomplete(answer: str) -> bool:
        cleaned = (answer or "").strip()
        if len(cleaned) < 20:
            return True
        if cleaned.endswith("...") or cleaned.endswith("\u2026"):
            return True
        if len(cleaned.split()) >= 6 and cleaned[-1:] not in {".", "!", "?"}:
            return True
        return False

    def generate_answer(
        self,
        *,
        prompt: str,
        system_instruction: str,
        language_code: str,
    ) -> str:
        full_system_instruction = (
            f"{system_instruction.strip()}\n{self.COMPLETE_RESPONSE_INSTRUCTION}"
        ).strip()

        def _request(client, model_name: str, *, retry_for_completion: bool = False) -> str:
            request_prompt = prompt
            if retry_for_completion:
                request_prompt = (
                    f"{prompt}\n\n"
                    "FINAL RESPONSE CHECK\n"
                    "- Re-answer fully in complete sentences.\n"
                    "- Do not end with an unfinished phrase or ellipsis.\n"
                    "- Keep the response concise but complete.\n"
                )
            response = client.models.generate_content(
                model=model_name,
                contents=request_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    temperature=0.25,
                    top_p=0.9,
                    max_output_tokens=768,
                ),
            )
            answer = (response.text or "").strip()
            if not answer:
                raise RuntimeError(f"Gemini returned an empty response for language {language_code}.")
            return answer

        answer = self._run_chat_with_fallback(
            "chat.generate_answer",
            lambda client, model_name: _request(client, model_name, retry_for_completion=False),
        )

        if self._looks_incomplete(answer):
            logger.warning(
                "[Gemini] chat.generate_answer returned a short or incomplete answer. Retrying once."
            )
            answer = self._run_chat_with_fallback(
                "chat.generate_answer.completion_retry",
                lambda client, model_name: _request(client, model_name, retry_for_completion=True),
            )

        return answer

    def transcribe_audio(
        self,
        *,
        file_path: Path,
        mime_type: str,
        preferred_language: str | None = None,
    ) -> dict[str, Any]:
        prompt = (
            "Transcribe this patient question for a healthcare education chatbot. "
            "Return strict JSON with keys transcript and language_code. "
            "Allowed language_code values: en, hi, kn, mr. "
            "Preserve the original spoken language. Do not answer the question."
        )
        if preferred_language:
            prompt += f" The likely language is {language_name(preferred_language)}."

        def _request(client, model_name: str) -> dict[str, Any]:
            uploaded_file = client.files.upload(file=str(file_path))
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, uploaded_file],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            raw = (response.text or "").strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Could not parse transcription JSON: {raw}") from exc

            transcript = str(parsed.get("transcript", "")).strip()
            language_code = str(parsed.get("language_code", preferred_language or "en")).strip().lower()
            if not transcript:
                raise RuntimeError("Transcription returned no text.")
            return {
                "transcript": transcript,
                "language_code": language_code,
                "mime_type": mime_type,
            }

        return self._run_tts_stt_with_fallback("audio.transcribe", _request)

    def synthesize_speech(
        self,
        *,
        text: str,
        language_code: str,
        destination: Path,
    ) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)

        def _request(client, model_name: str) -> None:
            response = client.models.generate_content(
                model=model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.settings.default_voice_name,
                            )
                        )
                    ),
                ),
            )

            try:
                pcm_data = response.candidates[0].content.parts[0].inline_data.data
            except Exception as exc:
                raise RuntimeError("Gemini TTS did not return inline audio data.") from exc

            with wave.open(str(destination), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(pcm_data)

        self._run_tts_stt_with_fallback(f"audio.synthesize[{language_code}]", _request)
