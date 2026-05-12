from __future__ import annotations

from rag_retriever import build_vector_index


def main() -> None:
    result = build_vector_index(force_rebuild=False)
    print("RAG vector index is ready.")
    print("Backend:", "FAISS")
    print("Indexed chunks:", result["count"])
    print("Index path:", result["index_path"])
    print("Reused existing index:", result["reused"])


if __name__ == "__main__":
    main()
