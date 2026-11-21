from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import evaluation.run_evaluation as evaluation
import rag_retriever as rag


class EndToEndEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rag.initialize_vector_resources()
        cls.index, cls.metadata = rag._loaded_resources
        cls.row_by_id = {row["chunk_id"]: index for index, row in enumerate(cls.metadata)}

    def _deterministic_query_embeddings(self, cases):
        by_question = {}
        for case in cases:
            ids = case["relevant_chunk_ids"]
            if ids:
                selected_id = ids[0]
            elif "exercise" in case["question"].lower() or "ವ್ಯಾಯಾಮ" in case["question"]:
                selected_id = "kb_0025_01"
            else:
                selected_id = "kb_0015_01"
            by_question[case["question"]] = self.index.reconstruct(self.row_by_id[selected_id])

        def embed(texts, *, is_query, titles=None):
            if not is_query:
                raise AssertionError("Evaluation must reuse the committed index, not rebuild it")
            return np.asarray([by_question[text] for text in texts], dtype=np.float32)

        return embed

    def test_dataset_references_approved_chunk_ids_and_expected_dimensions(self):
        cases = evaluation.load_cases()
        approved = {row["id"] for row in rag.load_prepared_chunks()}
        self.assertGreaterEqual(len(cases), 12)
        self.assertTrue({"en", "hi", "kn", "mr"}.issubset({case["language"] for case in cases}))
        self.assertTrue({"multi_document", "contradiction_probe", "numerical", "unanswerable"}.issubset(
            {case["question_type"] for case in cases}
        ))
        for case in cases:
            self.assertTrue(set(case["relevant_chunk_ids"]).issubset(approved), case["id"])

    def test_phase2_dataset_has_twenty_supported_questions_per_language_and_unsafe_set(self):
        fixture = Path(evaluation.__file__).parent / "cases_multilingual.json"
        cases = evaluation.load_cases(fixture)
        supported = [case for case in cases if case["expected_mode"] == "answerable"]
        counts = {language: sum(case["language"] == language for case in supported) for language in ("en", "hi", "kn", "mr")}
        self.assertEqual(counts, {"en": 20, "hi": 20, "kn": 20, "mr": 20})
        unsafe = [case for case in cases if case.get("question_type", "").startswith(("unsafe_", "prompt_injection"))]
        self.assertGreaterEqual(len(unsafe), 8)
        approved = {row["id"] for row in rag.load_prepared_chunks()}
        for case in supported:
            self.assertTrue(set(case["relevant_chunk_ids"]).issubset(approved), case["id"])

    def test_mocked_run_executes_graph_retrieval_generation_and_reporting(self):
        cases = evaluation.load_cases()
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(
                rag, "_embed_texts", side_effect=self._deterministic_query_embeddings(cases)
            ):
                report = evaluation.evaluate_cases(cases, mode="mock", output_dir=Path(temp))

            self.assertEqual(report["case_count"], len(cases))
            self.assertFalse(report["patient_data_used"])
            self.assertEqual(set(report["metrics_by_language"]), {"en", "hi", "kn", "mr"})
            self.assertTrue(all("retrieved" in row and "context_validation_status" in row for row in report["cases"]))
            self.assertTrue(all("score" in score for row in report["cases"] for score in row["retrieved"]))
            files = report["report_files"]
            self.assertTrue(Path(files["json"]).is_file())
            self.assertTrue(Path(files["markdown"]).is_file())
            saved = json.loads(Path(files["json"]).read_text(encoding="utf-8"))
            self.assertEqual(saved["case_count"], len(cases))
            markdown = Path(files["markdown"]).read_text(encoding="utf-8")
            self.assertIn("By Language", markdown)
            self.assertIn("Failure Cases", markdown)

    def test_generation_failure_is_separated_from_retrieval_and_guardrail_outcomes(self):
        case = dict(evaluation.load_cases()[0])
        case["mock_generation_error"] = "controlled provider outage"
        with patch.object(
            rag, "_embed_texts", side_effect=self._deterministic_query_embeddings([case])
        ):
            report = evaluation.evaluate_cases([case], mode="mock", output_dir=None)
        row = report["cases"][0]
        self.assertEqual(row["failure_stage"], "generation")
        self.assertIn("controlled provider outage", row["generation_error"])
        self.assertEqual(report["metrics"]["retrieval_failures"], 0)
        self.assertEqual(report["metrics"]["generation_failures"], 1)

    def test_live_mode_can_use_a_stubbed_gemini_service(self):
        class StubGemini:
            def generate_answer(self, **_kwargs):
                return "Chronic liver disease (CLD) means long-term liver damage that develops over time and can affect how the liver works."

        case = evaluation.load_cases()[0]
        with patch.object(
            rag, "_embed_texts", side_effect=self._deterministic_query_embeddings([case])
        ):
            report = evaluation.evaluate_cases(
                [case], mode="live", output_dir=None, gemini_service=StubGemini()
            )
        self.assertEqual(report["mode"], "live")
        self.assertEqual(report["cases"][0]["failure_stage"], None)


if __name__ == "__main__":
    unittest.main()
