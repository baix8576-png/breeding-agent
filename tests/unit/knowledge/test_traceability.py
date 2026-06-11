from __future__ import annotations

from pathlib import Path

from knowledge.runtime_store import KnowledgeRuntimeStore


def test_runtime_search_emits_minimal_trace_chain(tmp_path: Path) -> None:
    store = KnowledgeRuntimeStore(runtime_root=tmp_path / ".geneagent" / "knowledge")
    store.build_from_references(
        Path("references"),
        paths=[Path("references/papers/grm_core_papers_v1.md")],
    )

    result = store.search(
        "VanRaden genomic relationship matrix GBLUP",
        blueprint_scope="quantitative_genetics",
        limit=1,
        use_query_router=True,
    )

    assert result.trace is not None
    assert result.trace.schema_version == "knowledge_retrieval_trace.v1"
    assert result.trace.user_query == "VanRaden genomic relationship matrix GBLUP"
    assert result.trace.retrieval_filters.used_query_router is True
    assert result.trace.retrieval_filters.planned_blueprint_scope.value == "quantitative_genetics"
    assert result.trace.retrieval_filters.applied_blueprint_scope.value == "quantitative_genetics"
    assert result.trace.retrieved_chunks
    first_chunk = result.trace.retrieved_chunks[0]
    assert first_chunk.rank == 1
    assert first_chunk.doc_id == "paper_grm_vanraden_2008"
    assert first_chunk.chunk_id.startswith("paper_grm_vanraden_2008::")
    assert first_chunk.source_path == "references/papers/grm_core_papers_v1.md"
    assert first_chunk.page_or_anchor.startswith("#grm-01")
    assert first_chunk.evidence_level.value == "peer_reviewed"


def test_trace_records_metadata_fallbacks(tmp_path: Path) -> None:
    store = KnowledgeRuntimeStore(runtime_root=tmp_path / ".geneagent" / "knowledge")
    store.build_from_references(Path("references"))

    result = store.search(
        "猪 PigGTEx FarmGTEx eQTL regulatory variants literature DOI",
        limit=3,
        use_query_router=True,
    )

    assert result.trace is not None
    assert result.trace.retrieval_filters.planned_species == "pig"
    assert result.trace.retrieval_filters.metadata_fallbacks == result.metadata_fallbacks
    assert "dropped_evidence_source_filters" in result.trace.retrieval_filters.metadata_fallbacks
    assert result.trace.retrieved_chunks
    assert result.trace.retrieved_chunks[0].doc_id == result.hits[0].chunk.doc_id
