"""Offline-safe reranking for local knowledge search hits."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.knowledge import BlueprintScope, EvidenceLevel, KnowledgeSource
from knowledge.indexing import KnowledgeSearchHit, tokenize_knowledge_text
from knowledge.query_router import KnowledgeRetrievalPlan


class KnowledgeRerankConfig(BaseModel):
    """Configuration for deterministic local reranking."""

    schema_version: str = "knowledge_rerank_config.v1"
    mode: str = "offline_deterministic"
    blueprint_match_bonus: float = 0.6
    species_match_bonus: float = 0.35
    evidence_match_bonus: float = 0.25
    source_match_bonus: float = 0.25
    section_token_bonus: float = 0.05
    max_section_token_bonus: float = 0.3


class KnowledgeReranker:
    """Rerank hits without external embedding calls or network dependency."""

    def __init__(self, config: KnowledgeRerankConfig | None = None) -> None:
        self.config = config or KnowledgeRerankConfig()

    def rerank(
        self,
        *,
        query: str,
        hits: list[KnowledgeSearchHit],
        plan: KnowledgeRetrievalPlan | None = None,
        limit: int | None = None,
    ) -> list[KnowledgeSearchHit]:
        """Return hits with deterministic metadata/section bonuses applied."""

        if not hits:
            return []
        reranked = [self._rerank_hit(query=query, hit=hit, plan=plan) for hit in hits]
        reranked.sort(key=lambda hit: (-hit.score, hit.chunk.doc_id, hit.chunk.chunk_id))
        return reranked[:limit] if limit else reranked

    def _rerank_hit(
        self,
        *,
        query: str,
        hit: KnowledgeSearchHit,
        plan: KnowledgeRetrievalPlan | None,
    ) -> KnowledgeSearchHit:
        bonus, reasons = self._bonus(query=query, hit=hit, plan=plan)
        if bonus <= 0:
            return hit.model_copy(
                update={
                    "hit_reasons": [*hit.hit_reasons, f"rerank:{self.config.mode}", "rerank_bonus:0.000"],
                }
            )
        return hit.model_copy(
            update={
                "score": round(hit.score + bonus, 4),
                "confidence": min(1.0, round(hit.confidence + bonus / 10.0, 3)),
                "hit_reasons": [
                    *hit.hit_reasons,
                    f"rerank:{self.config.mode}",
                    f"rerank_bonus:{bonus:.3f}",
                    *reasons,
                ],
            }
        )

    def _bonus(
        self,
        *,
        query: str,
        hit: KnowledgeSearchHit,
        plan: KnowledgeRetrievalPlan | None,
    ) -> tuple[float, list[str]]:
        bonus = 0.0
        reasons: list[str] = []
        if plan and _matches_blueprint(hit.chunk.blueprint_scope, plan.blueprint_scope):
            bonus += self.config.blueprint_match_bonus
            reasons.append("rerank_blueprint_match")
        if plan and _matches_species(hit.chunk.species, plan.species):
            bonus += self.config.species_match_bonus
            reasons.append("rerank_species_match")
        if plan and _matches_evidence(hit.chunk.evidence_level, plan.evidence_levels):
            bonus += self.config.evidence_match_bonus
            reasons.append("rerank_evidence_match")
        if plan and _matches_source(hit.chunk.source, plan.sources):
            bonus += self.config.source_match_bonus
            reasons.append("rerank_source_match")

        query_tokens = set(tokenize_knowledge_text(query))
        section_tokens = set(tokenize_knowledge_text(f"{hit.chunk.section} {hit.chunk.doc_id}"))
        section_overlap = len(query_tokens & section_tokens)
        if section_overlap:
            section_bonus = min(
                self.config.max_section_token_bonus,
                section_overlap * self.config.section_token_bonus,
            )
            bonus += section_bonus
            reasons.append(f"rerank_section_overlap:{section_overlap}")
        return bonus, reasons


def _matches_blueprint(chunk_scope: BlueprintScope, plan_scope: BlueprintScope | None) -> bool:
    return plan_scope is not None and chunk_scope == plan_scope


def _matches_species(chunk_species: str, plan_species: str | None) -> bool:
    if not plan_species:
        return False
    return chunk_species.lower() in {"multi_species", plan_species.lower()}


def _matches_evidence(chunk_evidence: EvidenceLevel, planned_evidence: list[EvidenceLevel]) -> bool:
    return bool(planned_evidence) and chunk_evidence in planned_evidence


def _matches_source(chunk_source: KnowledgeSource, planned_sources: list[KnowledgeSource]) -> bool:
    return bool(planned_sources) and chunk_source in planned_sources
