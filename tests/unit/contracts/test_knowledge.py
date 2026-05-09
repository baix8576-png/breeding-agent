from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from contracts import (
    BlueprintScope,
    EvidenceLevel,
    KnowledgeChunk,
    KnowledgeIndexManifest,
    KnowledgeItemV2,
    KnowledgeSource,
)


def test_knowledge_item_v2_accepts_required_fields() -> None:
    item = KnowledgeItemV2(
        doc_id="paper_qc_missingness_2026_001",
        version="v2",
        species="sus_scrofa",
        blueprint_scope=BlueprintScope.QC,
        evidence_level=EvidenceLevel.PEER_REVIEWED,
        source=KnowledgeSource.PAPER,
        updated_at="2026-05-09T12:00:00+08:00",
        owner="popgen_quantgen",
    )

    assert item.doc_id == "paper_qc_missingness_2026_001"
    assert item.version == "v2"
    assert item.species == "sus_scrofa"
    assert item.blueprint_scope == BlueprintScope.QC
    assert item.evidence_level == EvidenceLevel.PEER_REVIEWED
    assert item.source == KnowledgeSource.PAPER
    assert isinstance(item.updated_at, datetime)
    assert item.owner == "popgen_quantgen"


def test_knowledge_item_v2_requires_source_field() -> None:
    with pytest.raises(ValidationError):
        KnowledgeItemV2(
            doc_id="sop_cluster_submission_001",
            version="v2",
            species="bos_taurus",
            blueprint_scope=BlueprintScope.SHARED,
            evidence_level=EvidenceLevel.SOP,
            updated_at="2026-05-09T12:00:00+08:00",
            owner="llm_orchestrator",
        )


def test_knowledge_item_v2_rejects_unknown_blueprint_scope() -> None:
    with pytest.raises(ValidationError):
        KnowledgeItemV2(
            doc_id="failure_case_001",
            version="v2",
            species="sus_scrofa",
            blueprint_scope="gwas",
            evidence_level=EvidenceLevel.INCIDENT_VERIFIED,
            source=KnowledgeSource.FAILURE_CASE,
            updated_at="2026-05-09T12:00:00+08:00",
            owner="popgen_quantgen",
        )


def test_knowledge_chunk_preserves_traceability_fields() -> None:
    chunk = KnowledgeChunk(
        chunk_id="paper_grm_vanraden_2008::grm-01",
        doc_id="paper_grm_vanraden_2008",
        source_path="references/papers/grm_core_papers_v1.md",
        blueprint_scope="grm",
        species="multi_species",
        evidence_level="peer_reviewed",
        source="paper",
        section="GRM-01 Foundational genomic relationship construction",
        page_or_anchor="#grm-01-foundational-genomic-relationship-construction",
        text="VanRaden genomic relationship matrix and GBLUP.",
        updated_at="2026-05-09T12:20:00+08:00",
        owner="popgen_quantgen",
        keywords=["vanraden", "grm", "gblup"],
        embedding_model="keyword-overlap-v1",
    )

    assert chunk.doc_id == "paper_grm_vanraden_2008"
    assert chunk.blueprint_scope == BlueprintScope.GRM
    assert chunk.evidence_level == EvidenceLevel.PEER_REVIEWED
    assert chunk.source == KnowledgeSource.PAPER
    assert chunk.page_or_anchor.startswith("#grm-01")


def test_knowledge_index_manifest_requires_non_negative_counts() -> None:
    manifest = KnowledgeIndexManifest(
        index_id="references-1-docs-1-chunks",
        created_at="2026-05-09T12:20:00+08:00",
        source_root="references",
        doc_count=1,
        chunk_count=1,
        bm25_index_path="memory://knowledge/bm25",
        embedding_index_path="memory://knowledge/embedding-lite",
        embedding_model="keyword-overlap-v1",
        sources=["references/papers/grm_core_papers_v1.md"],
    )

    assert manifest.schema_version == "knowledge_index_manifest.v1"
    assert manifest.metadata_schema == "knowledge_item.v2"
    assert manifest.chunk_count == 1

    with pytest.raises(ValidationError):
        KnowledgeIndexManifest(
            index_id="bad-index",
            created_at="2026-05-09T12:20:00+08:00",
            source_root="references",
            doc_count=-1,
            chunk_count=1,
        )
