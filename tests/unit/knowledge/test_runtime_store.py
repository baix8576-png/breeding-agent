from __future__ import annotations

from pathlib import Path

import pytest

from knowledge.runtime_store import KnowledgeRuntimeStore


SOURCE_FILE = Path("references/papers/grm_core_papers_v1.md")


def test_runtime_store_materializes_reference_chunks_and_manifest(tmp_path: Path) -> None:
    store = KnowledgeRuntimeStore(runtime_root=tmp_path / ".geneagent" / "knowledge")

    result = store.build_from_references(Path("references"), paths=[SOURCE_FILE])

    chunks_path = tmp_path / ".geneagent" / "knowledge" / "chunks" / "references.jsonl"
    manifest_path = tmp_path / ".geneagent" / "knowledge" / "indexes" / "manifest.json"
    assert chunks_path.is_file()
    assert manifest_path.is_file()
    assert result.errors == []
    assert result.manifest.metadata_schema == "knowledge_item.v2"
    assert result.manifest.doc_count == 10
    assert result.manifest.chunk_count == 10
    assert result.manifest.bm25_index_path is None
    assert result.manifest.embedding_index_path is None
    assert result.manifest.sources == ["references/papers/grm_core_papers_v1.md"]
    assert len(chunks_path.read_text(encoding="utf-8").splitlines()) == 10


def test_runtime_store_loads_searches_and_inspects_traceable_chunks(tmp_path: Path) -> None:
    store = KnowledgeRuntimeStore(runtime_root=tmp_path / ".geneagent" / "knowledge")
    store.build_from_references(Path("references"), paths=[SOURCE_FILE])

    chunks = store.load_chunks()
    assert len(chunks) == 10
    assert chunks[0].source_path == "references/papers/grm_core_papers_v1.md"

    search_result = store.search(
        "VanRaden genomic relationship matrix GBLUP",
        blueprint_scope="quantitative_genetics",
        limit=3,
    )
    assert search_result.chunk_count == 10
    assert search_result.hits
    assert search_result.hits[0].chunk.doc_id == "paper_grm_vanraden_2008"
    assert search_result.hits[0].chunk.page_or_anchor.startswith("#grm-01")

    inspection = store.inspect_doc("paper_grm_vanraden_2008")
    assert inspection.chunk_count == 1
    assert inspection.sources == ["references/papers/grm_core_papers_v1.md"]
    assert inspection.chunks[0].chunk_id.startswith("paper_grm_vanraden_2008::")


def test_runtime_store_rejects_references_as_runtime_root() -> None:
    with pytest.raises(ValueError, match="must not point inside references"):
        KnowledgeRuntimeStore(runtime_root=Path("references") / ".geneagent" / "knowledge")
