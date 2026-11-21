from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services.gemini_service import GeminiService


class GeminiCompletionTests(unittest.TestCase):
    def test_sdk_code_503_is_retryable(self):
        class GeminiServerError(Exception):
            code = 503

        retryable, reason = GeminiService._is_retryable_failure(
            GeminiService(SimpleNamespace()), GeminiServerError("UNAVAILABLE")
        )
        self.assertTrue(retryable)
        self.assertEqual(reason, "http 503")

    def test_unavailable_model_404_is_retryable_but_other_404_is_not(self):
        service = GeminiService(SimpleNamespace())

        class GeminiNotFound(Exception):
            code = 404

        unavailable, reason = service._is_retryable_failure(
            GeminiNotFound("Model is no longer available")
        )
        unrelated, _ = service._is_retryable_failure(GeminiNotFound("Resource not found"))

        self.assertTrue(unavailable)
        self.assertEqual(reason, "model unavailable (http 404)")
        self.assertFalse(unrelated)

    def test_unavailable_primary_model_switches_to_configured_fallback(self):
        service = GeminiService(SimpleNamespace(model_max_retry=0))
        service._ensure_client = lambda: object()
        calls = []

        class GeminiNotFound(Exception):
            code = 404

        def request_runner(_client, model_name):
            calls.append(model_name)
            if model_name == "primary":
                raise GeminiNotFound("Model is no longer available")
            return "fallback succeeded"

        result = service._run_with_model_fallback(
            models=["primary", "fallback"],
            mode_label="chat",
            operation_label="test",
            request_runner=request_runner,
        )

        self.assertEqual(result, "fallback succeeded")
        self.assertEqual(calls, ["primary", "fallback"])

    def test_transient_failure_retries_primary_then_uses_fallback(self):
        service = GeminiService(SimpleNamespace(model_max_retry=1))
        service._ensure_client = lambda: object()
        calls = []

        class GeminiServerError(Exception):
            code = 503

        def request_runner(_client, model_name):
            calls.append(model_name)
            if model_name == "primary":
                raise GeminiServerError("UNAVAILABLE")
            return "fallback answer"

        result = service._run_with_model_fallback(
            models=["primary", "fallback"],
            mode_label="chat",
            operation_label="test",
            request_runner=request_runner,
        )

        self.assertEqual(result, "fallback answer")
        self.assertEqual(calls, ["primary", "primary", "fallback"])

    def test_detects_unfinished_sentence_and_list_fragment(self):
        self.assertTrue(GeminiService._looks_incomplete("Sometimes gentle exercise can help * Sometimes"))
        self.assertTrue(GeminiService._looks_incomplete("For example, protein foods include:"))
        self.assertFalse(GeminiService._looks_incomplete("Gentle movement can help maintain strength."))

    def test_detects_token_limit_finish_reason(self):
        response = SimpleNamespace(candidates=[SimpleNamespace(finish_reason="MAX_TOKENS")])
        self.assertTrue(GeminiService._response_was_token_truncated(response))

    def test_still_incomplete_retry_uses_safe_language_fallback(self):
        service = GeminiService(SimpleNamespace())
        with patch.object(
            service,
            "_run_chat_with_fallback",
            side_effect=[
                {"text": "Gentle exercise can help because", "truncated": False},
                {"text": "Gentle exercise can help because", "truncated": False},
            ],
        ):
            answer = service.generate_answer(prompt="", system_instruction="", language_code="en")
        self.assertEqual(
            answer,
            "I couldn't complete that answer. Please ask again, and I'll explain it more briefly.",
        )


if __name__ == "__main__":
    unittest.main()
