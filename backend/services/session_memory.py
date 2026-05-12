from __future__ import annotations

from typing import Any


MAX_RECENT_MESSAGES = 3


def sanitize_message(value: str, limit: int = 320) -> str:
    cleaned = " ".join((value or "").strip().split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def build_memory_entry(
    question: str,
    answer: str,
    language: str,
    primary_topic: str,
) -> dict[str, str]:
    return {
        "question": sanitize_message(question, 180),
        "answer": sanitize_message(answer, 260),
        "language": language,
        "topic": primary_topic or "general",
    }


def summarize_entries(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for entry in entries:
        topic = entry.get("topic") or "general"
        question = entry.get("question") or ""
        answer = entry.get("answer") or ""
        lines.append(f"- Topic {topic}: patient asked '{question}'. Guidance given: {answer}")
    return "\n".join(lines)


def merge_into_summary(previous_summary: str, overflow_entries: list[dict[str, Any]]) -> str:
    extra = summarize_entries(overflow_entries)
    if previous_summary and extra:
        merged = f"{previous_summary}\n{extra}"
    else:
        merged = previous_summary or extra
    return sanitize_message(merged, limit=1200)


def roll_recent_messages(
    previous_messages: list[dict[str, Any]] | None,
    new_entry: dict[str, Any],
    previous_summary: str,
) -> tuple[list[dict[str, Any]], str]:
    messages = list(previous_messages or [])
    messages.append(new_entry)
    summary = previous_summary or ""

    if len(messages) > MAX_RECENT_MESSAGES:
        overflow = messages[:-MAX_RECENT_MESSAGES]
        messages = messages[-MAX_RECENT_MESSAGES:]
        summary = merge_into_summary(summary, overflow)

    return messages, summary
