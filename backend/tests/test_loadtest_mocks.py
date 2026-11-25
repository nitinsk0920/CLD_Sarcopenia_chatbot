from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import sys

import pytest

import services.gemini_service as gemini_service_module
from loadtest.config import loadtest_mock_mode_enabled, loadtest_request_requires_mock_rejection
from services.gemini_service import GeminiService


def test_mock_mode_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LOADTEST_MOCK_MODE", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    assert loadtest_mock_mode_enabled() is False


def test_locust_mock_requirement_header_only_rejects_and_never_enables():
    assert loadtest_request_requires_mock_rejection("true", mock_mode_enabled=False)
    assert not loadtest_request_requires_mock_rejection("true", mock_mode_enabled=True)
    assert not loadtest_request_requires_mock_rejection("", mock_mode_enabled=False)


def test_mock_mode_requires_explicit_local_environment(monkeypatch):
    monkeypatch.setenv("LOADTEST_MOCK_MODE", "true")
    monkeypatch.setenv("APP_ENV", "local")
    for marker in ("RENDER", "RENDER_SERVICE_ID", "DYNO", "K_SERVICE", "VERCEL", "AWS_LAMBDA_FUNCTION_NAME"):
        monkeypatch.delenv(marker, raising=False)
    assert loadtest_mock_mode_enabled() is True


@pytest.mark.parametrize("environment", ["production", "", "staging"])
def test_mock_mode_fails_closed_outside_local(monkeypatch, environment):
    monkeypatch.setenv("LOADTEST_MOCK_MODE", "true")
    monkeypatch.setenv("APP_ENV", environment)
    with pytest.raises(RuntimeError, match="restricted to local"):
        loadtest_mock_mode_enabled()


def test_mock_mode_fails_closed_when_deployment_marker_exists(monkeypatch):
    monkeypatch.setenv("LOADTEST_MOCK_MODE", "true")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("RENDER", "true")
    with pytest.raises(RuntimeError, match="RENDER"):
        loadtest_mock_mode_enabled()


def test_mock_mode_fails_closed_for_railway(monkeypatch):
    monkeypatch.setenv("LOADTEST_MOCK_MODE", "true")
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="RAILWAY_ENVIRONMENT"):
        loadtest_mock_mode_enabled()


def test_gemini_mock_path_never_initializes_google_client(tmp_path, monkeypatch):
    service = GeminiService(SimpleNamespace(default_voice_name="Kore"), loadtest_mock=True)

    def forbidden_client():
        raise AssertionError("mock path attempted a Gemini API client")

    monkeypatch.setattr(service, "_ensure_client", forbidden_client)
    answer = service.generate_answer(
        prompt=(
            "UNTRUSTED REFERENCE PASSAGES:\n"
            "<reference topic='sarcopenia'>Sarcopenia is the loss of muscle mass and muscle strength.</reference>"
        ),
        system_instruction="Education only.",
        language_code="en",
    )
    assert answer == "Sarcopenia is the loss of muscle mass and muscle strength."

    transcription = service.transcribe_audio(
        file_path=tmp_path / "synthetic.wav",
        mime_type="audio/wav",
        preferred_language="en",
    )
    assert transcription["transcript"] == "What is sarcopenia?"

    audio_path = tmp_path / "mock.wav"
    service.synthesize_speech(text=answer, language_code="en", destination=audio_path)
    assert audio_path.read_bytes().startswith(b"RIFF")
    assert service._client is None


def test_concurrent_mock_generation_keeps_request_passages_correlated(monkeypatch):
    service = GeminiService(SimpleNamespace(default_voice_name="Kore"), loadtest_mock=True)

    def forbidden_client():
        raise AssertionError("mock path attempted a Gemini API client")

    monkeypatch.setattr(service, "_ensure_client", forbidden_client)
    requests = [
        (
            "session-one",
            "<reference topic='sarcopenia'>Session one approved passage.</reference>",
        ),
        (
            "session-two",
            "<reference topic='nutrition'>Session two approved passage.</reference>",
        ),
    ]

    def generate(item):
        session_id, prompt = item
        return session_id, service.generate_answer(
            prompt=prompt,
            system_instruction="Education only.",
            language_code="en",
            request_id=session_id,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = dict(executor.map(generate, requests))

    assert results == {
        "session-one": "Session one approved passage.",
        "session-two": "Session two approved passage.",
    }
    assert service._client is None


@pytest.mark.parametrize("operation", ["generate", "tts", "stt"])
def test_local_mock_environment_blocks_real_gemini_provider_methods(monkeypatch, tmp_path, operation):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("LOADTEST_MOCK_MODE", "true")
    for marker in (
        "RENDER", "RENDER_SERVICE_ID", "RENDER_INSTANCE_ID", "DYNO", "HEROKU_APP_NAME",
        "K_SERVICE", "VERCEL", "VERCEL_ENV", "RAILWAY_ENVIRONMENT", "FLY_APP_NAME",
        "AWS_EXECUTION_ENV", "AWS_LAMBDA_FUNCTION_NAME", "CF_PAGES",
    ):
        monkeypatch.delenv(marker, raising=False)

    def forbidden_client(**_kwargs):
        raise AssertionError("Google client must not be constructed in local mock mode")

    monkeypatch.setattr(gemini_service_module.genai, "Client", forbidden_client)
    service = GeminiService(
        SimpleNamespace(
            gemini_api_key="test-only-not-a-real-key",
            model_timeout_ms=25_000,
            model_max_retry=0,
            gemini_model_primary="primary-model",
            gemini_model_fallback_1="fallback-model",
            gemini_model_fallback_2="",
            gemini_tts_model_primary="tts-model",
            gemini_tts_model_fallback_1="tts-fallback",
            gemini_tts_synthesis_model="gemini-3.8-flash-lite-tts",
            default_voice_name="Kore",
        ),
        loadtest_mock=False,
    )

    with pytest.raises(RuntimeError, match="External Gemini provider access is blocked"):
        if operation == "generate":
            service.generate_answer(prompt="question", system_instruction="education", language_code="en")
        elif operation == "tts":
            service.synthesize_speech(text="answer", language_code="en", destination=tmp_path / "blocked.wav")
        else:
            service.transcribe_audio(
                file_path=tmp_path / "blocked.wav", mime_type="audio/wav", preferred_language="en"
            )
    assert service._client is None


def test_mock_environment_uses_local_embeddings_even_without_startup_flag(monkeypatch):
    if sys.platform == "win32" and sys.version_info >= (3, 14):
        pytest.skip("The installed FAISS native extension fails to load on this Windows/Python 3.14 runtime.")
    import rag_retriever as rag

    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("LOADTEST_MOCK_MODE", "true")
    for marker in (
        "RENDER", "RENDER_SERVICE_ID", "RENDER_INSTANCE_ID", "DYNO", "HEROKU_APP_NAME",
        "K_SERVICE", "VERCEL", "VERCEL_ENV", "RAILWAY_ENVIRONMENT", "FLY_APP_NAME",
        "AWS_EXECUTION_ENV", "AWS_LAMBDA_FUNCTION_NAME", "CF_PAGES",
    ):
        monkeypatch.delenv(marker, raising=False)
    monkeypatch.setattr(rag, "_loadtest_mock_embeddings_enabled", False)
    monkeypatch.setattr(
        rag,
        "_get_embedding_client",
        lambda: (_ for _ in ()).throw(AssertionError("real Gemini embedding client was requested")),
    )

    embeddings = rag._embed_texts(["patient education question"], is_query=True)
    assert embeddings.shape == (1, rag.EMBED_DIM)
    with pytest.raises(RuntimeError, match="External Gemini embedding access is blocked"):
        rag._get_embedding_client()


def test_real_provider_client_factory_is_unchanged_without_mock_mode(monkeypatch):
    monkeypatch.delenv("LOADTEST_MOCK_MODE", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    sentinel = object()
    calls = []
    monkeypatch.setattr(
        gemini_service_module,
        "genai",
        SimpleNamespace(Client=lambda **kwargs: calls.append(kwargs) or sentinel),
    )
    monkeypatch.setattr(
        gemini_service_module,
        "types",
        SimpleNamespace(HttpOptions=lambda **kwargs: kwargs),
    )
    service = GeminiService(
        SimpleNamespace(gemini_api_key="unit-test-key", model_timeout_ms=25_000),
        loadtest_mock=False,
    )

    assert service._ensure_client() is sentinel
    assert len(calls) == 1


def test_retired_chat_fallbacks_are_not_used():
    service = GeminiService(
        SimpleNamespace(
            gemini_model_primary="gemini-2.5-flash",
            gemini_model_fallback_1="gemini-2.0-flash",
            gemini_model_fallback_2="gemini-1.5-flash",
        )
    )
    assert service._chat_models() == ["gemini-2.5-flash", "gemini-3.5-flash-lite"]


def test_loadtest_vector_fixture_uses_local_embeddings_without_api(monkeypatch):
    if sys.platform == "win32" and sys.version_info >= (3, 14):
        pytest.skip("The installed FAISS native extension fails to load on this Windows/Python 3.14 runtime.")
    try:
        import rag_retriever
    except ImportError as exc:
        pytest.skip(f"FAISS native extension is unavailable in this Python environment: {exc}")

    previous_resources = rag_retriever._loaded_resources
    previous_flag = rag_retriever._loadtest_mock_embeddings_enabled
    monkeypatch.setattr(
        rag_retriever,
        "_get_embedding_client",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected Gemini embedding call")),
    )
    try:
        rag_retriever.initialize_loadtest_mock_vector_resources()
        results = rag_retriever.retrieve_relevant_chunks("What is sarcopenia?", top_k=1)
        assert results["retrieved_chunks"]
        assert results["retrieved_chunks"][0]["chunk_id"]
    finally:
        rag_retriever._loaded_resources = previous_resources
        rag_retriever._loadtest_mock_embeddings_enabled = previous_flag
