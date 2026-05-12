from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

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

EMBED_DIM = 384
FAQ_CLOSE_MATCH_THRESHOLD = 0.82
TOPIC_KEYWORDS = {
    "cld": ["cld", "liver", "cirrhosis", "hepatic"],
    "sarcopenia": ["sarcopenia", "muscle", "weakness", "muscle loss"],
    "diet": ["diet", "protein", "protien", "food", "meal", "egg", "eggs", "dal", "paneer"],
    "exercise": ["exercise", "excercise", "walking", "walk", "activity", "training"],
    "safety": ["safe", "safety", "dizzy", "dizziness", "warning", "weak"],
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
    lowered = _expand_medical_aliases(text).lower().strip()
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered)
    return lowered


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _normalize_text(text))


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

            if best_item:
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


def _embed_text(text: str, dim: int = EMBED_DIM) -> np.ndarray:
    vector = np.zeros(dim, dtype=np.float32)
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if (digest[4] % 2 == 0) else -1.0
        vector[index] += sign

    norm = float(np.linalg.norm(vector))
    if norm > 0:
        vector /= norm

    return vector


def embed_texts(texts: list[str], dim: int = EMBED_DIM) -> np.ndarray:
    vectors = [_embed_text(text, dim=dim) for text in texts]
    if not vectors:
        return np.zeros((0, dim), dtype=np.float32)
    return np.vstack(vectors).astype(np.float32)


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
    embeddings = embed_texts(documents, dim=EMBED_DIM)

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
    }

    faiss.write_index(index, str(index_path))
    _save_json(metadata_path, metadata)
    _save_json(manifest_path, manifest)

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
        build_vector_index(persist_dir=store_dir, force_rebuild=False)

    index = faiss.read_index(str(index_path))
    metadata = _load_json(metadata_path)
    if not isinstance(metadata, list):
        raise ValueError("Metadata file is invalid. Expected list.")

    return index, metadata


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

    chunks = load_prepared_chunks()
    faq_entries = _build_faq_entries(chunks)
    faq_match = find_faq_match(question, faq_entries) if faq_first else None
    inferred_topics = _infer_query_topics(question)
    focus_topics = set(inferred_topics)
    if preferred_topics:
        focus_topics.update(topic for topic in preferred_topics if topic)

    index, metadata = _load_vector_resources(persist_dir=persist_dir)
    query_vec = embed_texts([question], dim=EMBED_DIM)

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
