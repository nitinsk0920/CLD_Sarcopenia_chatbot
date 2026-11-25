from __future__ import annotations

import base64
import io
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.gemini_service import GeminiService


TTS_MODEL = "gemini-3.8-flash-lite-tts"
MULTILINGUAL_TEST_TEXT = {
    "en": "Hello, this is a short audio test.",
    "hi": "नमस्ते, यह एक छोटा ऑडियो परीक्षण है।",
    "kn": "ನಮಸ್ಕಾರ, ಇದು ಚಿಕ್ಕ ಧ್ವನಿ ಪರೀಕ್ಷೆ.",
    "mr": "नमस्कार, ही एक छोटी ध्वनी चाचणी आहे.",
}


def _make_wav() -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(b"\x01\x00" * 240)
    return output.getvalue()


class FakeInteractions:
    def __init__(self, audio_data):
        self.audio_data = audio_data
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_audio=SimpleNamespace(data=self.audio_data))


def _service(interactions):
    service = GeminiService(
        SimpleNamespace(
            gemini_tts_synthesis_model=TTS_MODEL,
            default_voice_name="Kore",
            model_max_retry=0,
        )
    )
    client = SimpleNamespace(interactions=interactions)
    service._ensure_tts_client = lambda: client
    return service


@pytest.mark.parametrize("language", ["en", "hi", "kn", "mr"])
def test_tts_uses_gemini_38_lite_kore_and_saves_complete_wav(language, tmp_path):
    wav_bytes = _make_wav()
    interactions = FakeInteractions(base64.b64encode(wav_bytes).decode("ascii"))
    service = _service(interactions)
    destination = tmp_path / f"{language}.wav"

    service.synthesize_speech(
        text=MULTILINGUAL_TEST_TEXT[language],
        language_code=language,
        destination=destination,
    )

    assert len(interactions.calls) == 1
    call = interactions.calls[0]
    assert call["model"] == TTS_MODEL
    assert call["input"][0]["content"][0]["text"] == MULTILINGUAL_TEST_TEXT[language]
    assert call["response_format"] == {"type": "audio"}
    assert call["generation_config"]["speech_config"] == [{"voice": "Kore"}]
    assert destination.read_bytes() == wav_bytes
    with wave.open(str(destination), "rb") as generated:
        assert generated.getnchannels() == 1
        assert generated.getsampwidth() == 2
        assert generated.getframerate() == 24000
        assert generated.getnframes() > 0


@pytest.mark.parametrize("audio_data", [None, "not-base64!!!", base64.b64encode(b"not a wav").decode("ascii")])
def test_tts_fails_without_creating_empty_or_invalid_audio(audio_data, tmp_path):
    interactions = FakeInteractions(audio_data)
    service = _service(interactions)
    destination = tmp_path / "failed.wav"

    with pytest.raises(RuntimeError, match="Service temporarily unavailable"):
        service.synthesize_speech(
            text=MULTILINGUAL_TEST_TEXT["en"],
            language_code="en",
            destination=destination,
        )

    assert not destination.exists()
    assert not list(Path(tmp_path).glob("*.tmp"))


def test_tts_retries_transient_error_on_its_model_without_using_stt_fallbacks(tmp_path):
    wav_bytes = _make_wav()

    class RetryOnceInteractions:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                class TemporaryProviderFailure(Exception):
                    code = 503

                raise TemporaryProviderFailure("UNAVAILABLE")
            return SimpleNamespace(
                output_audio=SimpleNamespace(data=base64.b64encode(wav_bytes).decode("ascii"))
            )

    retrying_interactions = RetryOnceInteractions()

    service = _service(FakeInteractions(base64.b64encode(wav_bytes).decode("ascii")))
    service._ensure_tts_client = lambda: SimpleNamespace(interactions=retrying_interactions)
    service.settings.model_max_retry = 1
    destination = tmp_path / "retried.wav"

    service.synthesize_speech(
        text=MULTILINGUAL_TEST_TEXT["en"], language_code="en", destination=destination
    )

    assert len(retrying_interactions.calls) == 2
    assert [call["model"] for call in retrying_interactions.calls] == [TTS_MODEL, TTS_MODEL]
    assert destination.read_bytes() == wav_bytes
