from __future__ import annotations

from contracts.common import TaskDomain
from knowledge import KnowledgeResolver
from knowledge.retrieval import LocalKnowledgeRetriever, RetrievalDocument


class _StaticLocalRetriever:
    def __init__(self, hits: list[RetrievalDocument]) -> None:
        self._hits = hits

    def search(self, query: str, domain: TaskDomain, limit: int = 3) -> list[RetrievalDocument]:
        del query, domain, limit
        return list(self._hits)


class _CountingExternalRetriever:
    def __init__(self, hits: list[RetrievalDocument] | None = None) -> None:
        self.calls: list[tuple[str, TaskDomain]] = []
        self._hits = hits or [
            RetrievalDocument(
                source="external-fallback",
                title="External Fallback",
                summary="fallback",
            )
        ]

    def search(self, query: str, domain: TaskDomain) -> list[RetrievalDocument]:
        self.calls.append((query, domain))
        return list(self._hits)


class _FixedFallbackGate:
    def __init__(self, decision: str) -> None:
        self.decision = decision
        self.calls: list[dict[str, object]] = []

    def evaluate(
        self,
        *,
        query: str,
        domain: TaskDomain,
        coverage: str,
        local_hits: list[RetrievalDocument],
    ) -> str:
        self.calls.append(
            {
                "query": query,
                "domain": domain,
                "coverage": coverage,
                "local_hits": local_hits,
            }
        )
        return self.decision


def test_knowledge_resolver_stays_local_for_high_coverage_query() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="vcf phenotype pca admixture slurm",
        domain=TaskDomain.BIOINFORMATICS,
    )

    assert bundle.coverage == "high"
    assert bundle.fallback_used is False
    assert bundle.retrieval_mode == "local_only"
    assert bundle.external_hits == []
    assert len(bundle.local_hits) >= 2


def test_local_retriever_reads_reference_metadata_and_ranks_assets() -> None:
    retriever = LocalKnowledgeRetriever()

    hits = retriever.search(
        query="qc report template",
        domain=TaskDomain.BIOINFORMATICS,
        limit=3,
    )

    assert hits
    assert hits[0].source == "reference"
    assert hits[0].path == "references/report_templates/qc-report-template.md"
    assert "report_templates" in hits[0].tags


def test_local_retriever_emits_match_quality_fields() -> None:
    retriever = LocalKnowledgeRetriever()

    hits = retriever.search(
        query="qc report template phenotype",
        domain=TaskDomain.BIOINFORMATICS,
        limit=3,
    )

    assert hits
    top_hit = hits[0]
    assert hasattr(top_hit, "matched_tags")
    assert hasattr(top_hit, "matched_keywords")
    assert hasattr(top_hit, "hit_reasons")
    assert hasattr(top_hit, "confidence")
    assert isinstance(top_hit.matched_tags, list)
    assert isinstance(top_hit.matched_keywords, list)
    assert isinstance(top_hit.hit_reasons, list)
    assert isinstance(top_hit.confidence, float)
    assert 0.0 <= top_hit.confidence <= 1.0
    if top_hit.score > 0:
        assert top_hit.hit_reasons
        assert top_hit.matched_keywords or top_hit.matched_tags


def test_knowledge_resolver_uses_fallback_for_low_coverage_query() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="xqzv-404-zzzz",
        domain=TaskDomain.KNOWLEDGE,
    )

    assert bundle.coverage == "low"
    assert bundle.fallback_used is True
    assert bundle.retrieval_mode == "local_plus_external_fallback"
    assert len(bundle.external_hits) >= 1
    assert "fallback=external_fallback" in bundle.rationale


def test_knowledge_resolver_fallback_gate_allows_external_branch() -> None:
    local_retriever = _StaticLocalRetriever(
        hits=[
            RetrievalDocument(
                source="local",
                title="Partial local hit",
                summary="partial",
                tags=["shared", TaskDomain.KNOWLEDGE.value],
                keywords=["partial"],
                score=1,
            )
        ]
    )
    external_retriever = _CountingExternalRetriever()
    fallback_gate = _FixedFallbackGate(decision="allowed")
    resolver = KnowledgeResolver(
        local_retriever=local_retriever,
        external_retriever=external_retriever,
        fallback_gate=fallback_gate,
    )

    bundle = resolver.resolve(query="insufficient local coverage", domain=TaskDomain.KNOWLEDGE)

    assert bundle.coverage in {"low", "partial"}
    assert bundle.fallback_requested is True
    assert bundle.fallback_gate_decision == "allowed"
    assert bundle.fallback_used is True
    assert bundle.retrieval_mode == "local_plus_external_fallback"
    assert external_retriever.calls


def test_knowledge_resolver_fallback_gate_blocks_external_and_skips_external_call() -> None:
    local_retriever = _StaticLocalRetriever(
        hits=[
            RetrievalDocument(
                source="local",
                title="Partial local hit",
                summary="partial",
                tags=["shared", TaskDomain.KNOWLEDGE.value],
                keywords=["partial"],
                score=1,
            )
        ]
    )
    external_retriever = _CountingExternalRetriever()
    fallback_gate = _FixedFallbackGate(decision="blocked")
    resolver = KnowledgeResolver(
        local_retriever=local_retriever,
        external_retriever=external_retriever,
        fallback_gate=fallback_gate,
    )

    bundle = resolver.resolve(query="insufficient local coverage", domain=TaskDomain.KNOWLEDGE)

    assert bundle.coverage in {"low", "partial"}
    assert bundle.fallback_requested is True
    assert bundle.fallback_gate_decision == "blocked"
    assert bundle.fallback_used is False
    assert bundle.retrieval_mode == "local_only"
    assert bundle.external_hits == []
    assert external_retriever.calls == []


def test_knowledge_resolver_fallback_gate_not_requested_branch() -> None:
    local_retriever = _StaticLocalRetriever(
        hits=[
            RetrievalDocument(
                source="local",
                title="High local hit A",
                summary="high",
                tags=["shared", TaskDomain.BIOINFORMATICS.value],
                keywords=["vcf"],
                score=3,
            ),
            RetrievalDocument(
                source="local",
                title="High local hit B",
                summary="high",
                tags=["shared", TaskDomain.BIOINFORMATICS.value],
                keywords=["phenotype"],
                score=2,
            ),
        ]
    )
    external_retriever = _CountingExternalRetriever()
    fallback_gate = _FixedFallbackGate(decision="allowed")
    resolver = KnowledgeResolver(
        local_retriever=local_retriever,
        external_retriever=external_retriever,
        fallback_gate=fallback_gate,
    )

    bundle = resolver.resolve(query="vcf phenotype", domain=TaskDomain.BIOINFORMATICS)

    assert bundle.coverage == "high"
    assert bundle.fallback_requested is False
    assert bundle.fallback_gate_decision == "not_requested"
    assert bundle.fallback_used is False
    assert bundle.retrieval_mode == "local_only"
    assert bundle.external_hits == []
    assert external_retriever.calls == []


def test_knowledge_resolver_uses_reference_assets_before_fallback() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="dataset bundle template phenotype covariate pedigree",
        domain=TaskDomain.BIOINFORMATICS,
    )

    assert bundle.fallback_used is False
    assert bundle.retrieval_mode == "local_only"
    assert any(hit.source == "reference" for hit in bundle.local_hits)
    assert any(hit.path.endswith("dataset-bundle-template.md") for hit in bundle.local_hits)
