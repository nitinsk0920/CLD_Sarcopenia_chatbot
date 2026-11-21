from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import rag_retriever as rag


class FakeModels:
    def __init__(self, vectors=None, error=None):
        self.vectors = vectors or [[1.0] + [0.0] * (rag.EMBED_DIM - 1)]
        self.error = error
        self.calls = []

    def embed_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(embeddings=[SimpleNamespace(values=row) for row in self.vectors])


class GeminiFaissTests(unittest.TestCase):
    def test_everyday_food_and_activity_words_infer_existing_rag_topics(self):
        cases = {
            "Can I eat eggs or dal?": "diet",
            "मी अंडी किंवा डाळ खाऊ शकतो का?": "diet",
            "ನಾನು ಮೊಟ್ಟೆ ಅಥವಾ ಬೇಳೆ ತಿನ್ನಬಹುದೇ?": "diet",
            "क्या मैं अंडे या दाल खा सकता हूँ?": "diet",
            "What should I do if I feel dizzy during exercise?": "exercise",
            "व्यायाम के दौरान चक्कर आए तो मुझे क्या करना चाहिए?": "exercise",
            "ವ್ಯಾಯಾಮ ಮಾಡುವಾಗ ತಲೆಸುತ್ತು ಬಂದರೆ ನಾನು ಏನು ಮಾಡಬೇಕು?": "exercise",
            "व्यायाम करताना चक्कर आल्यास काय करावे?": "exercise",
        }
        for question, expected_topic in cases.items():
            self.assertIn(expected_topic, rag._infer_query_topics(question), question)
            self.assertGreater(rag._lexical_overlap_score(question, question), 0.0, question)

    def test_inner_product_of_normalized_vectors_is_cosine_similarity(self):
        index = rag.faiss.IndexFlatIP(2)
        index.add(np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))
        scores, indices = index.search(np.asarray([[0.8, 0.6]], dtype=np.float32), 2)
        self.assertEqual(indices.tolist(), [[0, 1]])
        self.assertTrue(np.allclose(scores[0], [0.8, 0.6]))

    def test_embedding_dimension_and_normalization(self):
        fake = FakeModels()
        with patch.object(rag, "_embedding_client", SimpleNamespace(models=fake)):
            vectors = rag._embed_texts(["test question"], is_query=True)
        self.assertEqual(vectors.shape, (1, 768))
        self.assertTrue(np.isfinite(vectors).all())
        self.assertAlmostEqual(float(np.linalg.norm(vectors[0])), 1.0)
        self.assertIn("task: question answering | query:", fake.calls[0]["contents"][0])

    def test_index_metadata_and_manifest_consistency(self):
        chunks = [{"id": "x1", "content": "health text", "topic": "cld", "subtopic": "intro", "source": "test"}]
        fake = FakeModels()
        with tempfile.TemporaryDirectory() as temp, patch.object(rag, "_embedding_client", SimpleNamespace(models=fake)):
            result = rag.build_vector_index(chunks=chunks, persist_dir=temp, force_rebuild=True)
            index, metadata = rag._load_vector_resources(temp)
            self.assertEqual(index.d, 768)
            self.assertEqual(index.ntotal, 1)
            self.assertEqual(len(metadata), 1)
            self.assertEqual(result["count"], 1)

    def test_embedding_rejects_wrong_dimension(self):
        fake = FakeModels(vectors=[[1.0, 0.0]])
        with patch.object(rag, "_embedding_client", SimpleNamespace(models=fake)), patch.object(rag.get_settings(), "model_max_retry", 0):
            with self.assertRaisesRegex(RuntimeError, "Gemini embedding request failed"):
                rag._embed_texts(["question"], is_query=True)

    def test_api_failure_is_bounded_and_does_not_fallback(self):
        fake = FakeModels(error=RuntimeError("API unavailable"))
        with patch.object(rag, "_embedding_client", SimpleNamespace(models=fake)), patch.object(rag.get_settings(), "model_max_retry", 1), patch.object(rag.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "Gemini embedding request failed"):
                rag._embed_texts(["question"], is_query=True)
        self.assertEqual(len(fake.calls), 2)


if __name__ == "__main__":
    unittest.main()
