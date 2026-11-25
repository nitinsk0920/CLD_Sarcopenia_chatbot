from __future__ import annotations

import base64
import html
import json
import logging
import os
import re
import tempfile
import wave
from io import BytesIO
from pathlib import Path
from typing import Any

from config import Settings
from loadtest.config import loadtest_mock_mode_enabled
from services.language_utils import language_name

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


logger = logging.getLogger(__name__)
VERIFIED_CHAT_FALLBACK = "gemini-3.5-flash-lite"
RETIRED_CHAT_FALLBACKS = {"gemini-2.0-flash", "gemini-1.5-flash"}


def _safe_diagnostic_detail(exc: Exception) -> str:
    detail = str(exc).replace("\n", " ").strip()
    detail = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED_KEY]", detail)
    detail = re.sub(r"(?i)Bearer\s+\S+", "Bearer [REDACTED]", detail)
    detail = re.sub(r"(?i)(postgres(?:ql)?://)[^\s@]+@", r"\1[REDACTED]@", detail)
    return detail[:300] or exc.__class__.__name__


class GeminiService:
    SERVICE_UNAVAILABLE_MESSAGE = "Service temporarily unavailable. Please try again shortly."
    COMPLETE_RESPONSE_INSTRUCTION = (
        "Provide complete, patient-friendly responses in clear full sentences. "
        "Do not abruptly stop mid-response."
    )

    def __init__(self, settings: Settings, *, loadtest_mock: bool = False):
        self.settings = settings
        self.loadtest_mock = loadtest_mock
        self._client = None
        self._tts_client = None

    def _ensure_client(self):
        if self.loadtest_mock or loadtest_mock_mode_enabled():
            raise RuntimeError(
                "External Gemini provider access is blocked while local load-test mocks are enabled."
            )
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

    def _ensure_tts_client(self):
        if self.loadtest_mock or loadtest_mock_mode_enabled():
            raise RuntimeError(
                "External Gemini provider access is blocked while local load-test mocks are enabled."
            )
        if genai is None or types is None:
            raise RuntimeError(
                "Missing Google Gen AI SDK. Install backend requirements before starting the server."
            )

        if not self._tts_client:
            if not self.settings.gemini_api_key and not (
                os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            ):
                raise RuntimeError(
                    "Gemini API key is not configured. Set GOOGLE_API_KEY or GEMINI_API_KEY."
                )
            self._tts_client = genai.Client(
                api_key=self.settings.gemini_api_key or None,
                http_options=types.HttpOptions(
                    api_version="v1beta",
                    client_args={"trust_env": False},
                    timeout=max(self.settings.model_timeout_ms, 1),
                ),
            )
        return self._tts_client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
        if self._tts_client is not None:
            self._tts_client.close()
            self._tts_client = None

    def _chat_models(self) -> list[str]:
        configured_fallbacks = [
            model
            for model in (
                self.settings.gemini_model_fallback_1,
                self.settings.gemini_model_fallback_2,
            )
            if (model or "").strip().lower() not in RETIRED_CHAT_FALLBACKS
            and (model or "").strip() == VERIFIED_CHAT_FALLBACK
        ]
        if not configured_fallbacks:
            configured_fallbacks = [VERIFIED_CHAT_FALLBACK]
        return self._dedupe_models([self.settings.gemini_model_primary, *configured_fallbacks])

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
        if status_code is None:
            status_code = getattr(exc, "code", None)
        if status_code in {408, 409, 425, 429, 500, 502, 503, 504}:
            return True, f"http {status_code}"

        message = str(exc).strip()
        lowered = message.lower()

        if status_code == 404 and "model" in lowered and any(
            marker in lowered
            for marker in ("not found", "not available", "no longer available", "not supported", "unsupported")
        ):
            return True, "model unavailable (http 404)"

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
        client_factory=None,
    ):
        if not models:
            raise RuntimeError("No Gemini models are configured.")

        client = (client_factory or self._ensure_client)()
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
                    logger.error(
                        "[Gemini] request failed operation=%s model=%s exception=%s "
                        "http_status=%s detail=%s retryable=%s",
                        operation_label,
                        model_name,
                        type(exc).__name__,
                        getattr(exc, "status_code", getattr(exc, "code", None)),
                        _safe_diagnostic_detail(exc),
                        retryable,
                    )
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
        if cleaned[-1:] not in {".", "!", "?", '"', "'", ")", "]", "}"}:
            return True
        if re.search(r"(?:\*\s*)?(?:and|or|but|because|such as|including|for example|sometimes|with|to|the|a|an)\s*$", cleaned, re.IGNORECASE):
            return True
        if re.search(r"(?:[-*#]|\d+[.)])\s*$", cleaned):
            return True
        return False

    @staticmethod
    def _response_was_token_truncated(response) -> bool:
        try:
            reason = response.candidates[0].finish_reason
        except (AttributeError, IndexError, TypeError):
            return False
        return "MAX_TOKENS" in str(reason).upper()

    @staticmethod
    def _incomplete_answer_message(language_code: str) -> str:
        messages = {
            "en": "I couldn't complete that answer. Please ask again, and I'll explain it more briefly.",
            "hi": "मैं उत्तर पूरा नहीं कर पाया। कृपया फिर से पूछें, मैं इसे संक्षेप में समझाऊँगा।",
            "kn": "ನಾನು ಉತ್ತರವನ್ನು ಪೂರ್ಣಗೊಳಿಸಲಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಕೇಳಿ, ಸಂಕ್ಷಿಪ್ತವಾಗಿ ವಿವರಿಸುತ್ತೇನೆ.",
            "mr": "मला उत्तर पूर्ण करता आले नाही. कृपया पुन्हा विचारा; मी थोडक्यात समजावून सांगेन.",
        }
        return messages.get(language_code, messages["en"])

    def generate_answer(
        self,
        *,
        prompt: str,
        system_instruction: str,
        language_code: str,
        request_id: str | None = None,
    ) -> str:
        if self.loadtest_mock:
            # Return approved corpus text verbatim so the real graph and output checks run
            # without invoking Gemini or pretending to measure its answer quality.
            references = re.findall(
                r"<reference\b[^>]*>(.*?)</reference>", prompt, flags=re.IGNORECASE | re.DOTALL
            )
            for reference in references:
                passage = html.unescape(re.sub(r"<[^>]+>", "", reference)).strip()
                if " | " in passage:
                    _, passage = passage.split(" | ", 1)
                if passage:
                    return passage
            return {
                "hi": "उपलब्ध शैक्षिक सामग्री में इस प्रश्न का पर्याप्त उत्तर नहीं है।",
                "kn": "ಲಭ್ಯವಿರುವ ಶೈಕ್ಷಣಿಕ ಮಾಹಿತಿಯಲ್ಲಿ ಈ ಪ್ರಶ್ನೆಗೆ ಸಾಕಷ್ಟು ಉತ್ತರ ಇಲ್ಲ.",
                "mr": "उपलब्ध शैक्षणिक माहितीत या प्रश्नाचे पुरेसे उत्तर नाही.",
            }.get(language_code, "The available educational material does not provide enough information.")

        full_system_instruction = (
            f"{system_instruction.strip()}\n{self.COMPLETE_RESPONSE_INSTRUCTION}"
        ).strip()

        def _request(client, model_name: str, *, retry_for_completion: bool = False) -> dict[str, Any]:
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
                    max_output_tokens=1024,
                ),
            )
            candidates = getattr(response, "candidates", None) or []
            finish_reason = None
            if candidates:
                finish_reason = getattr(candidates[0], "finish_reason", None)
            http_response = getattr(response, "sdk_http_response", None)
            http_status = getattr(http_response, "status_code", None)
            answer = (response.text or "").strip()
            logger.info(
                "[Gemini] response request_id=%s model=%s http_status=%s "
                "candidate_count=%s finish_reason=%s response_chars=%s",
                request_id or "untracked",
                model_name,
                http_status,
                len(candidates),
                str(finish_reason) if finish_reason is not None else "unknown",
                len(answer),
            )
            if not answer:
                raise RuntimeError(
                    f"Gemini returned an empty response for language {language_code}; "
                    f"candidate_count={len(candidates)} finish_reason={finish_reason}."
                )
            return {
                "text": answer,
                "truncated": self._response_was_token_truncated(response),
            }

        operation = f"chat.generate_answer request_id={request_id or 'untracked'}"
        result = self._run_chat_with_fallback(
            operation,
            lambda client, model_name: _request(client, model_name, retry_for_completion=False),
        )
        answer = result["text"]

        if result["truncated"] or self._looks_incomplete(answer):
            logger.warning(
                "[Gemini] chat.generate_answer returned a short or incomplete answer. Retrying once."
            )
            retry_result = self._run_chat_with_fallback(
                f"{operation}.completion_retry",
                lambda client, model_name: _request(client, model_name, retry_for_completion=True),
            )
            answer = retry_result["text"]
            if retry_result["truncated"] or self._looks_incomplete(answer):
                logger.error("[Gemini] completion retry was still incomplete; using a complete safe response.")
                return self._incomplete_answer_message(language_code)

        return answer

    def transcribe_audio(
        self,
        *,
        file_path: Path,
        mime_type: str,
        preferred_language: str | None = None,
    ) -> dict[str, Any]:
        if self.loadtest_mock:
            return {
                "transcript": "What is sarcopenia?",
                "language_code": preferred_language or "en",
                "mime_type": mime_type,
            }

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
        if self.loadtest_mock:
            # A short valid silent WAV exercises caching and file-serving paths only.
            with wave.open(str(destination), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(24000)
                wav_file.writeframes(b"\x00\x00" * 2400)
            return

        def _request(client, model_name: str) -> None:
            interaction = client.interactions.create(
                model=model_name,
                input=[{
                    "type": "user_input",
                    "content": [{"type": "text", "text": text}],
                }],
                response_format={"type": "audio"},
                generation_config={
                    "speech_config": [{"voice": self.settings.default_voice_name}],
                },
            )

            try:
                encoded_audio = interaction.output_audio.data
                if not encoded_audio:
                    raise ValueError("empty audio payload")
                wav_data = base64.b64decode(encoded_audio, validate=True)
            except Exception as exc:
                raise RuntimeError("Gemini TTS did not return valid encoded WAV audio.") from exc

            try:
                with wave.open(BytesIO(wav_data), "rb") as wav_file:
                    valid_wav = (
                        wav_data.startswith(b"RIFF")
                        and wav_data[8:12] == b"WAVE"
                        and wav_file.getnchannels() == 1
                        and wav_file.getsampwidth() == 2
                        and wav_file.getframerate() == 24000
                        and wav_file.getnframes() > 0
                    )
            except (wave.Error, EOFError) as exc:
                raise RuntimeError("Gemini TTS returned malformed WAV audio.") from exc
            if not valid_wav:
                raise RuntimeError(
                    "Gemini TTS returned WAV audio with an unsupported format or no frames."
                )

            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb", dir=destination.parent, suffix=".tmp", delete=False
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    temp_file.write(wav_data)
                os.replace(temp_path, destination)
            except OSError as exc:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
                raise RuntimeError("Could not save generated TTS WAV audio.") from exc

        self._run_with_model_fallback(
            models=[self.settings.gemini_tts_synthesis_model],
            mode_label="TTS",
            operation_label=f"audio.synthesize[{language_code}]",
            request_runner=_request,
            client_factory=self._ensure_tts_client,
        )
