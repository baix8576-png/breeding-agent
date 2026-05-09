from __future__ import annotations

from pathlib import Path

from contracts import BlueprintScope, EvidenceLevel
from knowledge.indexing import ReferenceKnowledgeIndexer


def test_reference_indexer_parses_paper_cards_into_knowledge_chunks() -> None:
    indexer = ReferenceKnowledgeIndexer(Path("references"))
    result = indexer.build(paths=[Path("references/papers/grm_core_papers_v1.md")])

    assert result.errors == []
    assert result.manifest.metadata_schema == "knowledge_item.v2"
    assert result.manifest.doc_count == 10
    assert result.manifest.chunk_count == 10
    assert result.manifest.bm25_index_path == "memory://knowledge/bm25"
    assert result.manifest.embedding_model == "keyword-overlap-v1"

    first_chunk = result.chunks[0]
    assert first_chunk.doc_id == "paper_grm_vanraden_2008"
    assert first_chunk.blueprint_scope == BlueprintScope.GRM
    assert first_chunk.evidence_level == EvidenceLevel.PEER_REVIEWED
    assert first_chunk.source_path == "references/papers/grm_core_papers_v1.md"
    assert first_chunk.page_or_anchor.startswith("#grm-01")
    assert {"vanraden", "grm"}.issubset(set(first_chunk.keywords))


def test_hybrid_index_returns_bm25_embedding_and_traceable_hits() -> None:
    index = ReferenceKnowledgeIndexer(Path("references")).build_index(
        paths=[Path("references/papers/grm_core_papers_v1.md")]
    )

    hits = index.search(
        "VanRaden genomic relationship matrix GBLUP",
        blueprint_scope=BlueprintScope.GRM,
        limit=3,
    )

    assert hits
    top_hit = hits[0]
    assert top_hit.chunk.doc_id == "paper_grm_vanraden_2008"
    assert top_hit.chunk.chunk_id.startswith("paper_grm_vanraden_2008::")
    assert top_hit.bm25_score > 0
    assert top_hit.embedding_score > 0
    assert top_hit.confidence > 0
    assert any(reason.startswith("bm25_match:") for reason in top_hit.hit_reasons)
    assert any(reason.startswith("embedding_overlap:") for reason in top_hit.hit_reasons)
