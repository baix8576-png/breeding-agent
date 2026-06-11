"""Traceability models for local-first knowledge retrieval."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from contracts.knowledge import BlueprintScope, EvidenceLevel, KnowledgeSource
from knowledge.indexing import KnowledgeSearchHit
from knowledge.query_router import KnowledgeRetrievalPlan


class RetrievalFilterTrace(BaseModel):
    """Metadata filters requested and finally applied during retrieval."""

    planned_blueprint_scope: BlueprintScope | None = None
    planned_species: str | None = None
    planned_evidence_levels: list[EvidenceLevel] = Field(default_factory=list)
    planned_sources: list[KnowledgeSource] = Field(default_factory=list)
    applied_blueprint_scope: BlueprintScope | None = None
    applied_species: str | None = None
    applied_evidence_levels: list[EvidenceLevel] = Field(default_factory=list)
    applied_sources: list[KnowledgeSource] = Field(default_factory=list)
    used_query_router: bool = False
    metadata_fallbacks: list[str] = Field(default_factory=list)


class RetrievedChunkTrace(BaseModel):
    """Minimal trace for one retrieved chunk used as evidence."""

    rank: int = Field(ge=1)
    score: float
    confidence: float
    doc_id: str = Field(min_length=3)
    chunk_id: str = Field(min_length=3)
    source_path: str = Field(min_length=3)
    page_or_anchor: str = Field(min_length=1)
    section: str = Field(min_length=1)
    species: str = Field(min_length=2)
    blueprint_scope: BlueprintScope
    evidence_level: EvidenceLevel
    source: KnowledgeSource
    hit_reasons: list[str] = Field(default_factory=list)


class KnowledgeRetrievalTrace(BaseModel):
    """Auditable evidence chain for one local knowledge retrieval request."""

    schema_version: str = "knowledge_retrieval_trace.v1"
    created_at: datetime
    user_query: str = Field(min_length=1)
    intended_use: str = "retrieval_only"
    final_answer_or_plan_ref: str | None = None
    retrieval_filters: RetrievalFilterTrace
    retrieved_chunks: list[RetrievedChunkTrace] = Field(default_factory=list)


def build_retrieval_trace(
    *,
    user_query: str,
    plan: KnowledgeRetrievalPlan | None,
    applied_blueprint_scope: BlueprintScope | None,
    applied_species: str | None,
    applied_evidence_levels: list[EvidenceLevel],
    applied_sources: list[KnowledgeSource],
    used_query_router: bool,
    metadata_fallbacks: list[str],
    hits: list[KnowledgeSearchHit],
    intended_use: str = "retrieval_only",
    final_answer_or_plan_ref: str | None = None,
) -> KnowledgeRetrievalTrace:
    """Build a trace payload from routed filters and scored hits."""

    return KnowledgeRetrievalTrace(
        created_at=datetime.now(timezone.utc),
        user_query=user_query,
        intended_use=intended_use,
        final_answer_or_plan_ref=final_answer_or_plan_ref,
        retrieval_filters=RetrievalFilterTrace(
            planned_blueprint_scope=plan.blueprint_scope if plan else None,
            planned_species=plan.species if plan else None,
            planned_evidence_levels=plan.evidence_levels if plan else [],
            planned_sources=plan.sources if plan else [],
            applied_blueprint_scope=applied_blueprint_scope,
            applied_species=applied_species,
            applied_evidence_levels=applied_evidence_levels,
            applied_sources=applied_sources,
            used_query_router=used_query_router,
            metadata_fallbacks=metadata_fallbacks,
        ),
        retrieved_chunks=[
            RetrievedChunkTrace(
                rank=index,
                score=hit.score,
                confidence=hit.confidence,
                doc_id=hit.chunk.doc_id,
                chunk_id=hit.chunk.chunk_id,
                source_path=hit.chunk.source_path,
                page_or_anchor=hit.chunk.page_or_anchor,
                section=hit.chunk.section,
                species=hit.chunk.species,
                blueprint_scope=hit.chunk.blueprint_scope,
                evidence_level=hit.chunk.evidence_level,
                source=hit.chunk.source,
                hit_reasons=hit.hit_reasons,
            )
            for index, hit in enumerate(hits, start=1)
        ],
    )
