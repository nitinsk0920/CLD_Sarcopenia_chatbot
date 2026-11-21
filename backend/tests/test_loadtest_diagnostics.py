from io import BytesIO
import wave

import pytest

from loadtest.diagnostics import classify_chat_response, make_synthetic_wav, mask_session_id


VALID_BODY = {
    "session_id": "session-12345678",
    "answer_id": "answer-1",
    "answer": "Sarcopenia involves loss of muscle mass and strength.",
    "selected_topics": ["sarcopenia"],
    "response_language": "en",
    "retrieved_chunks": [],
    "safety": {},
}


@pytest.mark.parametrize(
    ("status", "body", "invalid_json", "expected"),
    [
        (500, {}, False, "http_error"),
        (200, None, True, "invalid_json_response"),
        (200, {**VALID_BODY, "answer": None}, False, "missing_assistant_response"),
        (200, {**VALID_BODY, "answer": "  "}, False, "empty_assistant_response"),
        (200, {**VALID_BODY, "answer": "Service temporarily unavailable."}, False, "generic_fallback_response"),
        (200, {key: value for key, value in VALID_BODY.items() if key != "safety"}, False, "unexpected_response_schema"),
        (200, {**VALID_BODY, "session_id": "some-other-session"}, False, "patient_session_ownership_mismatch"),
        (200, {**VALID_BODY, "response_language": "hi"}, False, "other_validation_failure"),
    ],
)
def test_chat_failure_categories(status, body, invalid_json, expected):
    result = classify_chat_response(
        status_code=status,
        body=body,
        expected_session_id=VALID_BODY["session_id"],
        invalid_json=invalid_json,
    )
    assert result is not None
    assert result[0] == expected


def test_chat_response_passes_when_schema_and_session_match():
    assert classify_chat_response(
        status_code=200,
        body=VALID_BODY,
        expected_session_id=VALID_BODY["session_id"],
    ) is None


def test_synthetic_audio_fixture_is_valid_pcm_wav():
    wav_bytes = make_synthetic_wav()
    with wave.open(BytesIO(wav_bytes), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() == 16_000
        assert audio.getnframes() > 0


def test_session_mask_does_not_expose_middle_identifier():
    assert mask_session_id("12345678-abcdefgh") == "1234...efgh"
