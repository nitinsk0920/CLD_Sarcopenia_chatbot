from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
import time
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types

from config import get_settings
from loadtest.config import loadtest_mock_mode_enabled

try:
    import faiss
    import numpy as np
except ImportError as exc:
    raise ImportError(
        "Missing RAG dependencies. Install with: pip install -r backend/requirements-rag.txt"
    ) from exc


BASE_DIR = Path(__file__).resolve().parents[1]
PREPARED_CHUNKS_PATH = BASE_DIR / "backend" / "data" / "knowledge_ready_for_embedding.json"
VECTOR_STORE_DIR = BASE_DIR / "backend" / "vector_store" / "faiss"
FAISS_INDEX_PATH = VECTOR_STORE_DIR / "knowledge.index"
METADATA_PATH = VECTOR_STORE_DIR / "knowledge_metadata.json"
MANIFEST_PATH = VECTOR_STORE_DIR / "manifest.json"

EMBED_DIM = get_settings().gemini_embedding_dimension
EMBED_MODEL = get_settings().gemini_embedding_model
logger = logging.getLogger(__name__)
_embedding_client = None
_loaded_resources: tuple[Any, list[dict[str, Any]]] | None = None
_loadtest_mock_embeddings_enabled = False
FAQ_CLOSE_MATCH_THRESHOLD = 0.82
TOPIC_KEYWORDS = {
    "cld": ["cld", "liver", "cirrhosis", "hepatic", "यकृत", "लिवर", "ಯಕೃತ್ತು", "ಯಕೃತ್ತಿನ", "yakrut"],
    "sarcopenia": ["sarcopenia", "muscle", "weakness", "weak", "tired", "fatigue", "muscle loss", "मांसपेश", "कमजोरी", "थकान", "स्नायू", "अशक्तपणा", "थकवा", "ಸ್ನಾಯು", "ದೌರ್ಬಲ್ಯ", "ದಣಿವು", "ಅಶಕ್ತತೆ"],
    "diet": ["diet", "nutrition", "protein", "protien", "food", "foods", "meal", "eat", "egg", "eggs", "dal", "lentil", "pulse", "paneer", "milk", "yogurt", "fish", "chicken", "tofu", "अंडा", "अंडे", "दाल", "खाना", "पनीर", "आहार", "पोषण", "प्रोटीन", "प्रथिने", "अंडी", "डाळ", "खाद्यपदार्थ", "ಮೊಟ್ಟೆ", "ಬೇಳೆ", "ಆಹಾರ", "ಪೋಷಣೆ", "ಪ್ರೋಟೀನ್", "ಹಾಲು", "ಪನೀರ್"],
    "exercise": ["exercise", "excercise", "walking", "walk", "activity", "training", "strength", "व्यायाम", "चालणे", "शक्ती", "ವ್ಯಾಯಾಮ", "ನಡೆಯುವುದು", "ಶಕ್ತಿ"],
    "safety": ["safe", "safety", "dizzy", "dizziness", "warning", "चक्कर", "सुरक्षा", "सुरक्षित", "ಎಚ್ಚರಿಕೆ", "ತಲೆಸುತ್ತು", "धोका", "अशक्तपणा"],
}


@dataclass
class FAQMatch:
    chunk_id: str
    question: str
    answer: str
    topic: str
    source: str
    score: float
    match_type: str


def _expand_medical_aliases(text: str) -> str:
    expanded = text
    expanded = re.sub(r"\bcld\b", " chronic liver disease ", expanded, flags=re.IGNORECASE)
    return expanded


def _normalize_text(text: str) -> str:
    lowered = unicodedata.normalize("NFC", _expand_medical_aliases(text).casefold()).strip()
    lowered = "".join(
        char if char.isspace() or unicodedata.category(char)[0] in {"L", "N", "M"} else " "
        for char in lowered
    )
    return re.sub(r"\s+", " ", lowered, flags=re.UNICODE).strip()


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    for char in _normalize_text(text):
        category = unicodedata.category(char)[0]
        if category in {"L", "N"} or (category == "M" and current):
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tokens


def _infer_query_topics(question: str) -> list[str]:
    q = _normalize_text(question)
    found: list[str] = []
    for topic, words in TOPIC_KEYWORDS.items():
        if any(word in q for word in words):
            found.append(topic)
    return found


def _infer_single_topic(text: str) -> str:
    topics = _infer_query_topics(text)
    return topics[0] if topics else ""


def _is_definition_query(question: str) -> bool:
    q = _normalize_text(question)
    definition_patterns = [
        "what is",
        "what is the meaning",
        "meaning of",
        "define",
        "explain",
        "क्या है",
        "क्या मतलब",
        "ಎಂದರೇನು",
        "ಅರ್ಥವೇನು",
        "म्हणजे काय",
        "अर्थ काय",
    ]
    return any(pattern in q for pattern in definition_patterns)


def _lexical_overlap_score(question: str, content: str) -> float:
    q_tokens = set(_tokenize(question))
    c_tokens = set(_tokenize(content))
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = len(q_tokens & c_tokens) / max(1, len(q_tokens))
    return float(overlap)


def _is_medical_knowledge_chunk(chunk: dict[str, Any]) -> bool:
    # Exclude chatbot behavior/policy instructions from retrieval context.
    subtopic = str(chunk.get("subtopic", "")).strip().lower()
    content = str(chunk.get("content", "")).strip().lower()
    if subtopic == "education_only":
        return False
    if "chatbot is for education" in content:
        return False
    return True


def _parse_faq_content(content: str) -> tuple[str, str]:
    match = re.match(r"^\s*Q:\s*(.*?)\s*A:\s*(.*?)\s*$", content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        plain = content.strip()
        return plain, plain
    question = match.group(1).strip()
    answer = match.group(2).strip()
    return question, answer


def _build_data_signature(chunks: list[dict[str, Any]]) -> str:
    minimal = [{"id": row["id"], "content": row["content"]} for row in chunks]
    payload = json.dumps(minimal, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_prepared_chunks(path: str | Path = PREPARED_CHUNKS_PATH) -> list[dict[str, Any]]:
    with Path(path).resolve().open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, list):
        raise ValueError("Prepared chunks file must be a list.")

    chunks = [chunk for chunk in raw if isinstance(chunk, dict)]
    return [chunk for chunk in chunks if _is_medical_knowledge_chunk(chunk)]


def _build_faq_entries(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    faq_chunks = [chunk for chunk in chunks if chunk.get("topic") == "faq"]
    faq_entries: list[dict[str, Any]] = []

    for chunk in faq_chunks:
        question, answer = _parse_faq_content(str(chunk.get("content", "")))
        faq_entries.append(
            {
                "chunk_id": str(chunk.get("id", "")),
                "question": question,
                "question_norm": _normalize_text(question),
                "faq_topic": _infer_single_topic(question),
                "answer": answer,
                "topic": str(chunk.get("topic", "")),
                "source": str(chunk.get("source", "")),
            }
        )

    return faq_entries


def find_faq_match(
    question: str,
    faq_entries: list[dict[str, Any]],
    min_similarity: float = FAQ_CLOSE_MATCH_THRESHOLD,
) -> FAQMatch | None:
    query_norm = _normalize_text(question)
    if not query_norm:
        return None
    query_topics = _infer_query_topics(query_norm)

    # Priority path: if the user asks for a definition of a known topic,
    # force FAQ selection within that topic first.
    if query_topics and _is_definition_query(query_norm):
        for topic in query_topics:
            topic_faqs = [item for item in faq_entries if item.get("faq_topic") == topic]
            if not topic_faqs:
                continue

            best_item: dict[str, Any] | None = None
            best_score = 0.0
            for item in topic_faqs:
                score = SequenceMatcher(None, query_norm, item["question_norm"]).ratio()
                if score > best_score:
                    best_score = score
                    best_item = item

            if best_item and best_score >= min_similarity:
                return FAQMatch(
                    chunk_id=best_item["chunk_id"],
                    question=best_item["question"],
                    answer=best_item["answer"],
                    topic=best_item["topic"],
                    source=best_item["source"],
                    score=round(best_score, 4),
                    match_type="topic_definition",
                )

    for item in faq_entries:
        if query_norm == item["question_norm"]:
            return FAQMatch(
                chunk_id=item["chunk_id"],
                question=item["question"],
                answer=item["answer"],
                topic=item["topic"],
                source=item["source"],
                score=1.0,
                match_type="exact",
            )

    # Substring / token-overlap shortcut for short FAQ style questions.
    query_tokens = set(_tokenize(query_norm))
    best_overlap_item: dict[str, Any] | None = None
    best_overlap_score = 0.0
    for item in faq_entries:
        qn = item["question_norm"]
        if query_norm in qn or qn in query_norm:
            return FAQMatch(
                chunk_id=item["chunk_id"],
                question=item["question"],
                answer=item["answer"],
                topic=item["topic"],
                source=item["source"],
                score=0.95,
                match_type="substring",
            )

        faq_tokens = set(_tokenize(qn))
        if not query_tokens or not faq_tokens:
            continue
        overlap = len(query_tokens & faq_tokens) / max(1, len(query_tokens))
        if overlap > best_overlap_score:
            best_overlap_score = overlap
            best_overlap_item = item

    if best_overlap_item is not None and best_overlap_score >= 0.6:
        return FAQMatch(
            chunk_id=best_overlap_item["chunk_id"],
            question=best_overlap_item["question"],
            answer=best_overlap_item["answer"],
            topic=best_overlap_item["topic"],
            source=best_overlap_item["source"],
            score=round(best_overlap_score, 4),
            match_type="token_overlap",
        )

    best_item: dict[str, Any] | None = None
    best_score = 0.0
    for item in faq_entries:
        score = SequenceMatcher(None, query_norm, item["question_norm"]).ratio()
        if score > best_score:
            best_score = score
            best_item = item

    if best_item is None or best_score < min_similarity:
        return None

    return FAQMatch(
        chunk_id=best_item["chunk_id"],
        question=best_item["question"],
        answer=best_item["answer"],
        topic=best_item["topic"],
        source=best_item["source"],
        score=round(best_score, 4),
        match_type="close",
    )


def _get_embedding_client():
    global _embedding_client
    if loadtest_mock_mode_enabled():
        raise RuntimeError(
            "External Gemini embedding access is blocked while local load-test mocks are enabled."
        )
    if _embedding_client is None:
        api_key = get_settings().gemini_api_key
        if not api_key:
            raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY to use Gemini embeddings.")
        _embedding_client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=get_settings().model_timeout_ms),
        )
    return _embedding_client


def _mock_embedding(text: str) -> np.ndarray:
    """Stable local-only hashing vectors; never mixed with the persisted Gemini index."""
    tokens = _tokenize(text)
    features = list(tokens) + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    vector = np.zeros((EMBED_DIM,), dtype=np.float32)
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
        bucket = int.from_bytes(digest[:8], "little") % EMBED_DIM
        vector[bucket] += 1.0 if digest[8] & 1 else -1.0
    norm = float(np.linalg.norm(vector))
    if norm:
        vector /= norm
    return vector


def _embed_texts(texts: list[str], *, is_query: bool, titles: list[str] | None = None) -> np.ndarray:
    if not texts:
        return np.zeros((0, EMBED_DIM), dtype=np.float32)
    if _loadtest_mock_embeddings_enabled or loadtest_mock_mode_enabled():
        return np.stack([_mock_embedding(text) for text in texts]).astype(np.float32)
    if titles is None:
        titles = [""] * len(texts)
    formatted = [
        f"task: question answering | query: {text}" if is_query
        else f"title: {title or 'Health education'} | text: {text}"
        for text, title in zip(texts, titles)
    ]
    last_error = None
    retries = max(0, min(get_settings().model_max_retry, 1))
    for attempt in range(retries + 1):
        try:
            response = _get_embedding_client().models.embed_content(
                model=EMBED_MODEL,
                contents=formatted,
                config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM),
            )
            vectors = np.asarray([item.values for item in response.embeddings], dtype=np.float32)
            if vectors.shape != (len(texts), EMBED_DIM):
                raise ValueError(f"Gemini returned embedding shape {vectors.shape}; expected {(len(texts), EMBED_DIM)}")
            if not np.isfinite(vectors).all():
                raise ValueError("Gemini returned non-finite embedding values.")
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError("Gemini returned an empty embedding vector.")
            return (vectors / norms).astype(np.float32)
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                logger.warning("Gemini embedding attempt failed; retrying once (%s).", type(exc).__name__)
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError("Gemini embedding request failed; retrieval cannot continue.") from last_error


def _save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_vector_index(
    chunks: list[dict[str, Any]] | None = None,
    persist_dir: str | Path = VECTOR_STORE_DIR,
    force_rebuild: bool = False,
) -> dict[str, Any]:
    docs = chunks or load_prepared_chunks()
    store_dir = Path(persist_dir).resolve()
    store_dir.mkdir(parents=True, exist_ok=True)

    index_path = store_dir / FAISS_INDEX_PATH.name
    metadata_path = store_dir / METADATA_PATH.name
    manifest_path = store_dir / MANIFEST_PATH.name

    signature = _build_data_signature(docs)
    if (
        not force_rebuild
        and index_path.exists()
        and metadata_path.exists()
        and manifest_path.exists()
    ):
        manifest = _load_json(manifest_path)
        if (
            manifest.get("signature") == signature
            and int(manifest.get("count", -1)) == len(docs)
            and int(manifest.get("dim", -1)) == EMBED_DIM
        ):
            return {
                "index_path": str(index_path),
                "metadata_path": str(metadata_path),
                "manifest_path": str(manifest_path),
                "count": len(docs),
                "dimension": EMBED_DIM,
                "signature": signature,
                "reused": True,
            }

    documents = [str(item.get("content", "")) for item in docs]
    titles = [f"{item.get('topic', '')} / {item.get('subtopic', '')} ({item.get('source', '')})" for item in docs]
    embeddings = _embed_texts(documents, is_query=False, titles=titles)

    index = faiss.IndexFlatIP(EMBED_DIM)
    if len(embeddings):
        index.add(embeddings)

    metadata: list[dict[str, Any]] = []
    for item in docs:
        metadata.append(
            {
                "chunk_id": str(item.get("id", "")),
                "topic": str(item.get("topic", "")),
                "subtopic": str(item.get("subtopic", "")),
                "source": str(item.get("source", "")),
                "content": str(item.get("content", "")),
            }
        )

    manifest = {
        "signature": signature,
        "count": len(docs),
        "dim": EMBED_DIM,
        "embedding_model": EMBED_MODEL,
        "similarity_metric": "cosine_similarity (normalized vectors + inner product)",
        "source_content_hash": signature,
        "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }
    if index.ntotal != len(metadata) or index.d != EMBED_DIM:
        raise ValueError("Refusing to save inconsistent FAISS index and metadata.")
    if not np.isfinite(embeddings).all():
        raise ValueError("Refusing to save non-finite embeddings.")
    staged = Path(tempfile.mkdtemp(prefix="faiss-build-", dir=store_dir))
    try:
        staged_index = staged / index_path.name
        staged_metadata = staged / metadata_path.name
        staged_manifest = staged / manifest_path.name
        faiss.write_index(index, str(staged_index))
        _save_json(staged_metadata, metadata)
        _save_json(staged_manifest, manifest)
        faiss.read_index(str(staged_index))
        if len(_load_json(staged_metadata)) != index.ntotal:
            raise ValueError("Staged metadata count does not match FAISS vectors.")
        os.replace(staged_index, index_path)
        os.replace(staged_metadata, metadata_path)
        os.replace(staged_manifest, manifest_path)
    finally:
        import shutil
        shutil.rmtree(staged, ignore_errors=True)

    return {
        "index_path": str(index_path),
        "metadata_path": str(metadata_path),
        "manifest_path": str(manifest_path),
        "count": len(docs),
        "dimension": EMBED_DIM,
        "signature": signature,
        "reused": False,
    }


def _load_vector_resources(
    persist_dir: str | Path = VECTOR_STORE_DIR,
) -> tuple[Any, list[dict[str, Any]]]:
    store_dir = Path(persist_dir).resolve()
    index_path = store_dir / FAISS_INDEX_PATH.name
    metadata_path = store_dir / METADATA_PATH.name
    manifest_path = store_dir / MANIFEST_PATH.name

    if not (index_path.exists() and metadata_path.exists() and manifest_path.exists()):
        raise RuntimeError(f"Prebuilt Gemini FAISS index is missing in {store_dir}. Run `python build_rag_index.py` offline.")

    index = faiss.read_index(str(index_path))
    metadata = _load_json(metadata_path)
    if not isinstance(metadata, list):
        raise ValueError("Metadata file is invalid. Expected list.")
    manifest = _load_json(manifest_path)
    if index.d != EMBED_DIM or manifest.get("dim") != EMBED_DIM or manifest.get("embedding_model") != EMBED_MODEL:
        raise ValueError(f"FAISS index/model mismatch; expected {EMBED_MODEL} with {EMBED_DIM} dimensions. Rebuild the index.")
    if index.ntotal != len(metadata) or manifest.get("count") != len(metadata):
        raise ValueError("FAISS index vector count does not match metadata records.")

    return index, metadata


def initialize_vector_resources(persist_dir: str | Path = VECTOR_STORE_DIR) -> None:
    """Load and validate the committed index once during backend startup."""
    global _loaded_resources, _loadtest_mock_embeddings_enabled
    if loadtest_mock_mode_enabled():
        raise RuntimeError(
            "Local load-test mock mode is enabled; refusing to load persisted Gemini embeddings."
        )
    _loaded_resources = _load_vector_resources(persist_dir)
    _loadtest_mock_embeddings_enabled = False


def initialize_loadtest_mock_vector_resources() -> None:
    """Build a process-local fixture index; this never reads/writes Gemini vectors."""
    global _loaded_resources, _loadtest_mock_embeddings_enabled
    chunks = load_prepared_chunks()
    metadata = [
        {
            "chunk_id": str(item.get("id", "")),
            "topic": str(item.get("topic", "")),
            "subtopic": str(item.get("subtopic", "")),
            "source": str(item.get("source", "")),
            "content": str(item.get("content", "")),
        }
        for item in chunks
    ]
    _loadtest_mock_embeddings_enabled = True
    vectors = _embed_texts([item["content"] for item in metadata], is_query=False)
    index = faiss.IndexFlatIP(EMBED_DIM)
    if len(vectors):
        index.add(vectors)
    _loaded_resources = (index, metadata)


def retrieve_relevant_chunks(
    user_question: str,
    top_k: int = 3,
    faq_first: bool = True,
    preferred_topics: list[str] | None = None,
    persist_dir: str | Path = VECTOR_STORE_DIR,
) -> dict[str, Any]:
    question = user_question.strip()
    if not question:
        return {"query": user_question, "faq_first_match": None, "retrieved_chunks": []}

    if loadtest_mock_mode_enabled() and not _loadtest_mock_embeddings_enabled:
        raise RuntimeError(
            "Local load-test mock mode is enabled, but the matching temporary mock FAISS index was not initialized."
        )

    chunks = load_prepared_chunks()
    faq_entries = _build_faq_entries(chunks)
    faq_match = find_faq_match(question, faq_entries) if faq_first else None
    inferred_topics = _infer_query_topics(question)
    focus_topics = set(inferred_topics)
    if preferred_topics:
        focus_topics.update(topic for topic in preferred_topics if topic)

    if persist_dir == VECTOR_STORE_DIR and _loaded_resources is not None:
        index, metadata = _loaded_resources
    else:
        index, metadata = _load_vector_resources(persist_dir=persist_dir)
    query_vec = _embed_texts([question], is_query=True)

    search_k = max(top_k * 5, 15)
    scores, indices = index.search(query_vec, search_k)

    candidates: list[dict[str, Any]] = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue

        row = metadata[idx]
        if faq_match and row.get("chunk_id") == faq_match.chunk_id:
            continue

        semantic_score = float(score)
        overlap_score = _lexical_overlap_score(question, str(row.get("content", "")))
        row_topic = row.get("topic", "")
        if focus_topics:
            topic_boost = 0.28 if row_topic in focus_topics else -0.08
        else:
            topic_boost = 0.0
        final_score = (semantic_score * 0.55) + (overlap_score * 0.45) + topic_boost

        candidates.append(
            {
                "chunk_id": row.get("chunk_id", ""),
                "topic": row.get("topic", ""),
                "subtopic": row.get("subtopic", ""),
                "source": row.get("source", ""),
                "content": row.get("content", ""),
                "score": round(final_score, 4),
                "semantic_score": round(semantic_score, 4),
                "overlap_score": round(overlap_score, 4),
            }
        )

    candidates.sort(key=lambda item: item["score"], reverse=True)
    retrieved = candidates[:top_k]

    return {
        "query": user_question,
        "faq_first_match": faq_match.__dict__ if faq_match else None,
        "retrieved_chunks": retrieved,
    }


if __name__ == "__main__":
    info = build_vector_index(force_rebuild=False)
    print("FAISS index ready.")
    print("Indexed chunks:", info["count"])
    print("Reused existing index:", info["reused"])
