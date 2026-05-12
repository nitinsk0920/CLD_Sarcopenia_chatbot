from __future__ import annotations

import json
from pathlib import Path

from knowledge_loader import load_and_prepare_knowledge


def main() -> None:
    bundle = load_and_prepare_knowledge()

    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "backend" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    embedding_path = output_dir / "knowledge_ready_for_embedding.json"
    retrieval_path = output_dir / "knowledge_retrieval_index.json"
    validation_path = output_dir / "knowledge_validation_summary.json"

    embedding_path.write_text(
        json.dumps(bundle.prepared_chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    retrieval_path.write_text(
        json.dumps(bundle.retrieval_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    validation_path.write_text(
        json.dumps(bundle.validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("Knowledge base source:", bundle.source_path)
    print("Entries loaded:", bundle.validation["total_entries"])
    print("Prepared chunks:", len(bundle.prepared_chunks))
    print("Required topics present:", ", ".join(bundle.validation["required_topics_present"]))
    if bundle.validation["required_topics_missing"]:
        print("Required topics missing:", ", ".join(bundle.validation["required_topics_missing"]))
    else:
        print("Required topics missing: none")
    print("Validation status:", "PASS" if bundle.validation["is_valid"] else "CHECK NEEDED")
    print("Embedding output:", embedding_path)
    print("Retrieval output:", retrieval_path)
    print("Validation output:", validation_path)


if __name__ == "__main__":
    main()
