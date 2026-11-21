from __future__ import annotations

from rag_retriever import build_vector_index
from knowledge_loader import load_and_prepare_knowledge


def main() -> None:
    bundle = load_and_prepare_knowledge()
    if not bundle.validation["is_valid"]:
        raise RuntimeError(f"Knowledge base validation failed: {bundle.validation}")
    result = build_vector_index(chunks=bundle.prepared_chunks, force_rebuild=True)
    print("RAG vector index is ready.")
    print("Backend:", "FAISS")
    print("Indexed chunks:", result["count"])
    print("Index path:", result["index_path"])
    print("Reused existing index:", result["reused"])
    print("Embedding model: Gemini Embedding 2")
    print("Embedding dimension:", result["dimension"])


if __name__ == "__main__":
    main()
