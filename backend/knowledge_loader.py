from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_KB_PATH = (
    Path(__file__).resolve().parents[1] / "src" / "data" / "cld_sarcopenia_rag_refined.json"
)

REQUIRED_TOPICS = {"cld", "sarcopenia", "diet", "exercise", "safety", "faq"}

TOPIC_ALIASES = {
    "cld": "cld",
    "cld_basics": "cld",
    "chronic_liver_disease": "cld",
    "sarcopenia": "sarcopenia",
    "sarcopenia_basics": "sarcopenia",
    "diet": "diet",
    "diet_and_protein": "diet",
    "nutrition": "diet",
    "protein": "diet",
    "exercise": "exercise",
    "physical_activity": "exercise",
    "safety": "safety",
    "faq": "faq",
}


@dataclass
class KnowledgeBundle:
    source_path: str
    validation: dict[str, Any]
    prepared_chunks: list[dict[str, Any]]
    retrieval_index: dict[str, list[dict[str, Any]]]


def _slug(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]+", "", normalized)
    return normalized


def normalize_topic(topic: str) -> str:
    key = _slug(topic)
    return TOPIC_ALIASES.get(key, key)


def _light_refine_text(text: str) -> str:
    # Keep source knowledge unchanged in meaning; only clean spacing.
    refined = re.sub(r"\s+", " ", text or "").strip()
    return refined


def _split_long_text(text: str, max_chars: int = 420) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [part.strip() for part in sentences if part.strip()]
    if not sentences:
        return [text]

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = sentence
        else:
            # Hard split if single sentence itself is too long.
            for start in range(0, len(sentence), max_chars):
                chunks.append(sentence[start : start + max_chars].strip())
            current = ""

    if current:
        chunks.append(current)

    return chunks or [text]


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_raw_chunks(path: str | Path = DEFAULT_KB_PATH) -> tuple[list[dict[str, Any]], Path]:
    kb_path = Path(path).resolve()
    raw_data = _read_json(kb_path)

    if isinstance(raw_data, dict) and isinstance(raw_data.get("chunks"), list):
        raw_chunks = raw_data["chunks"]
    elif isinstance(raw_data, list):
        raw_chunks = raw_data
    else:
        raise ValueError(
            "Unsupported knowledge file shape. Expected list[...] or dict with 'chunks'."
        )

    if not all(isinstance(row, dict) for row in raw_chunks):
        raise ValueError("Each knowledge entry must be an object with 'topic' and 'content'.")

    return raw_chunks, kb_path


def validate_structure(raw_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    missing_topic = 0
    missing_content = 0
    raw_topics: dict[str, int] = {}
    normalized_topics: dict[str, int] = {}

    for row in raw_chunks:
        topic_raw = str(row.get("topic", "")).strip()
        content = str(row.get("content", "")).strip()

        if not topic_raw:
            missing_topic += 1
        if not content:
            missing_content += 1

        if topic_raw:
            raw_topics[topic_raw] = raw_topics.get(topic_raw, 0) + 1
            norm = normalize_topic(topic_raw)
            normalized_topics[norm] = normalized_topics.get(norm, 0) + 1

    missing_required_topics = sorted(REQUIRED_TOPICS - set(normalized_topics.keys()))

    return {
        "total_entries": len(raw_chunks),
        "missing_topic_count": missing_topic,
        "missing_content_count": missing_content,
        "raw_topics": raw_topics,
        "normalized_topic_counts": normalized_topics,
        "required_topics_present": sorted(REQUIRED_TOPICS - set(missing_required_topics)),
        "required_topics_missing": missing_required_topics,
        "is_valid": missing_topic == 0 and missing_content == 0 and not missing_required_topics,
    }


def prepare_for_embedding(
    raw_chunks: list[dict[str, Any]], max_chars: int = 420
) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    row_index = 0

    for row in raw_chunks:
        row_index += 1
        topic_raw = str(row.get("topic", "")).strip()
        if not topic_raw:
            continue

        content = _light_refine_text(str(row.get("content", "")))
        if not content:
            continue

        topic = normalize_topic(topic_raw)
        subtopic = _slug(str(row.get("subtopic", "")).strip() or "general")
        source = str(row.get("source", "")).strip() or "unknown"
        text_parts = _split_long_text(content, max_chars=max_chars)

        for part_index, part in enumerate(text_parts, start=1):
            prepared.append(
                {
                    "id": f"kb_{row_index:04d}_{part_index:02d}",
                    "topic": topic,
                    "topic_raw": topic_raw,
                    "subtopic": subtopic,
                    "content": part,
                    "source": source,
                    "metadata": {
                        "topic": topic,
                        "topic_raw": topic_raw,
                        "subtopic": subtopic,
                        "source": source,
                    },
                }
            )

    return prepared


def build_retrieval_index(
    prepared_chunks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for chunk in prepared_chunks:
        topic = chunk["topic"]
        index.setdefault(topic, []).append(chunk)
    return index


def load_and_prepare_knowledge(path: str | Path = DEFAULT_KB_PATH) -> KnowledgeBundle:
    raw_chunks, source_path = load_raw_chunks(path)
    validation = validate_structure(raw_chunks)
    prepared_chunks = prepare_for_embedding(raw_chunks)
    retrieval_index = build_retrieval_index(prepared_chunks)

    return KnowledgeBundle(
        source_path=str(source_path),
        validation=validation,
        prepared_chunks=prepared_chunks,
        retrieval_index=retrieval_index,
    )
