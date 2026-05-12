from __future__ import annotations

import json
import sys

from rag_retriever import retrieve_relevant_chunks


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = "Can I eat eggs or dal every day?"

    result = retrieve_relevant_chunks(question, top_k=3, faq_first=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
