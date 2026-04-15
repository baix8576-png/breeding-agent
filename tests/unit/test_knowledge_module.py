from __future__ import annotations

from contracts.common import TaskDomain
from knowledge import KnowledgeResolver


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


def test_knowledge_resolver_uses_fallback_for_low_coverage_query() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="no matching keyword for this lookup",
        domain=TaskDomain.KNOWLEDGE,
    )

    assert bundle.coverage == "low"
    assert bundle.fallback_used is True
    assert bundle.retrieval_mode == "local_plus_external_placeholder"
    assert len(bundle.external_hits) >= 1
    assert "fallback=external_placeholder" in bundle.rationale
