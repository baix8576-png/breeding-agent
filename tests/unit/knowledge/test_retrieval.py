from __future__ import annotations

from contracts.common import TaskDomain
from knowledge import KnowledgeResolver
from knowledge.retrieval import LocalKnowledgeRetriever


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


def test_knowledge_resolver_uses_fallback_for_low_coverage_query() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="xqzv-404-zzzz",
        domain=TaskDomain.KNOWLEDGE,
    )

    assert bundle.coverage == "low"
    assert bundle.fallback_used is True
    assert bundle.retrieval_mode == "local_plus_external_placeholder"
    assert len(bundle.external_hits) >= 1
    assert "fallback=external_placeholder" in bundle.rationale


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
