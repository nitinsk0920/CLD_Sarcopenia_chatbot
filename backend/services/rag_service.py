from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rag_retriever import retrieve_relevant_chunks


@dataclass(slots=True)
class FaissKnowledgeService:
    def search(
        self,
        question: str,
        preferred_topics: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        return retrieve_relevant_chunks(
            user_question=question,
            top_k=top_k,
            faq_first=True,
            preferred_topics=preferred_topics,
        )
