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


def _extract_action_commands(summary: str) -> dict[str, str]:
    action_commands: dict[str, str] = {}
    for chunk in summary.split(" | "):
        if not chunk.startswith("action_id="):
            continue
        action, separator, command = chunk.partition(";command=")
        if not separator:
            continue
        action_commands[action.replace("action_id=", "", 1).strip()] = command.strip()
    return action_commands


def _local_retriever_with_catalog(catalog: list[RetrievalDocument]) -> LocalKnowledgeRetriever:
    retriever = LocalKnowledgeRetriever()
    retriever._catalog = catalog
    return retriever


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


def test_local_retriever_scheduler_errors_return_structured_actionable_guidance() -> None:
    scheduler_diagnostic = RetrievalDocument(
        source="reference",
        path="references/system/scheduler-error-recipes.md",
        title="Scheduler Error Recipes",
        summary=(
            "action_id=check_scheduler_cli;command=command -v sbatch || command -v qsub | "
            "action_id=check_submit_acl;command=id && groups | "
            "action_id=check_job_visibility;command=squeue -j <job_id> || qstat <job_id>"
        ),
        tags=["reference", "shared", TaskDomain.SYSTEM.value, "diagnostic", "scheduler"],
        keywords=[
            "sbatch",
            "qsub",
            "permission",
            "denied",
            "command",
            "not",
            "found",
            "job",
            "missing",
            "squeue",
            "sacct",
            "qstat",
        ],
    )
    generic_system_note = RetrievalDocument(
        source="local",
        title="General System Guidance",
        summary="Use standard runtime checks for service health and environment drift.",
        tags=["shared", TaskDomain.SYSTEM.value],
        keywords=["system", "health", "runtime"],
    )
    retriever = _local_retriever_with_catalog([scheduler_diagnostic, generic_system_note])

    hits = retriever.search(
        query="sbatch command not found qsub permission denied job not found",
        domain=TaskDomain.SYSTEM,
        limit=2,
    )

    assert hits
    top_hit = hits[0]
    assert top_hit.path == "references/system/scheduler-error-recipes.md"
    assert top_hit.score > 0
    assert {"sbatch", "qsub", "permission", "job"}.issubset(set(top_hit.matched_keywords))
    assert any(reason.startswith("keyword_match:") for reason in top_hit.hit_reasons)

    command_map = _extract_action_commands(top_hit.summary)
    assert {"check_scheduler_cli", "check_submit_acl", "check_job_visibility"}.issubset(
        set(command_map.keys())
    )
    assert command_map["check_scheduler_cli"] == "command -v sbatch || command -v qsub"
    assert command_map["check_job_visibility"] == "squeue -j <job_id> || qstat <job_id>"


def test_local_retriever_bio_tool_errors_return_command_level_guidance() -> None:
    tool_diagnostic = RetrievalDocument(
        source="reference",
        path="references/bioinformatics/tool-error-recipes.md",
        title="Bioinformatics Tool Error Recipes",
        summary=(
            "action_id=plink2_input;command=plink2 --bfile <prefix> --make-bed --out <out_prefix> | "
            "action_id=bcftools_index;command=bcftools index -f <input.vcf.gz> | "
            "action_id=vcftools_input;command=vcftools --gzvcf <input.vcf.gz> --out <out_prefix> | "
            "action_id=gcta_input;command=gcta64 --bfile <prefix> --make-grm --out <out_prefix>"
        ),
        tags=["reference", "shared", TaskDomain.BIOINFORMATICS.value, "diagnostic", "tool_error"],
        keywords=[
            "plink2",
            "bcftools",
            "vcftools",
            "gcta",
            "input",
            "index",
            "failed",
            "missing",
            "cannot",
            "open",
        ],
    )
    generic_bio_note = RetrievalDocument(
        source="local",
        title="Bioinformatics Workflow Primer",
        summary="Start from input validation, then run qc and structure analysis in sequence.",
        tags=["shared", TaskDomain.BIOINFORMATICS.value],
        keywords=["workflow", "validation", "qc", "pca"],
    )
    retriever = _local_retriever_with_catalog([tool_diagnostic, generic_bio_note])

    hits = retriever.search(
        query="plink2 failed input bcftools index missing vcftools cannot open gcta input",
        domain=TaskDomain.BIOINFORMATICS,
        limit=2,
    )

    assert hits
    top_hit = hits[0]
    assert top_hit.path == "references/bioinformatics/tool-error-recipes.md"
    assert top_hit.score > 0
    assert {"plink2", "bcftools", "vcftools", "gcta", "index", "input"}.issubset(
        set(top_hit.matched_keywords)
    )
    assert any(reason.startswith("keyword_match:") for reason in top_hit.hit_reasons)

    command_map = _extract_action_commands(top_hit.summary)
    assert {"plink2_input", "bcftools_index", "vcftools_input", "gcta_input"}.issubset(
        set(command_map.keys())
    )
    assert command_map["plink2_input"].startswith("plink2 --bfile")
    assert command_map["bcftools_index"] == "bcftools index -f <input.vcf.gz>"
    assert command_map["gcta_input"].startswith("gcta64 --bfile")


def test_local_retriever_non_error_query_does_not_raise_diagnostic_false_positive() -> None:
    diagnostic_doc = RetrievalDocument(
        source="reference",
        path="references/bioinformatics/tool-error-recipes.md",
        title="Bioinformatics Tool Error Recipes",
        summary=(
            "action_id=plink2_input;command=plink2 --bfile <prefix> --make-bed --out <out_prefix>"
        ),
        tags=["reference", "shared", TaskDomain.BIOINFORMATICS.value, "diagnostic", "tool_error"],
        keywords=["plink2", "bcftools", "vcftools", "gcta", "error", "index", "input"],
    )
    normal_doc = RetrievalDocument(
        source="reference",
        path="references/modeling_guides/genomic-prediction-overview.md",
        title="Genomic Prediction Overview",
        summary="Plan genomic prediction with validation folds and trait-level metrics.",
        tags=["reference", "shared", TaskDomain.BIOINFORMATICS.value],
        keywords=["genomic", "prediction", "validation", "metrics", "workflow"],
    )
    retriever = _local_retriever_with_catalog([diagnostic_doc, normal_doc])

    hits = retriever.search(
        query="genomic prediction validation workflow design",
        domain=TaskDomain.BIOINFORMATICS,
        limit=3,
    )
    positive_hits = [hit for hit in hits if hit.score > 0]

    assert positive_hits
    assert all("diagnostic" not in hit.tags for hit in positive_hits)
    assert all(not _extract_action_commands(hit.summary) for hit in positive_hits)


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


def test_knowledge_resolver_knowledge_only_policy_blocks_bio_domain_external_fallback() -> None:
    local_retriever = _StaticLocalRetriever(hits=[])
    external_retriever = _CountingExternalRetriever()
    resolver = KnowledgeResolver(
        local_retriever=local_retriever,
        external_retriever=external_retriever,
        external_fallback_policy="knowledge_only",
    )

    bundle = resolver.resolve(query="xqzv-404-bio", domain=TaskDomain.BIOINFORMATICS)

    assert bundle.fallback_requested is True
    assert bundle.fallback_gate_decision == "blocked"
    assert bundle.fallback_gate_reason == "policy_knowledge_only_blocks_domain"
    assert bundle.fallback_used is False
    assert bundle.retrieval_mode == "local_only"
    assert bundle.external_hits == []
    assert external_retriever.calls == []


def test_knowledge_resolver_diagnostic_only_policy_requires_system_error_intent() -> None:
    local_retriever = _StaticLocalRetriever(hits=[])
    external_retriever = _CountingExternalRetriever()
    resolver = KnowledgeResolver(
        local_retriever=local_retriever,
        external_retriever=external_retriever,
        external_fallback_policy="diagnostic_only",
    )

    blocked_bundle = resolver.resolve(
        query="summarize local references",
        domain=TaskDomain.SYSTEM,
    )
    assert blocked_bundle.fallback_requested is True
    assert blocked_bundle.fallback_gate_decision == "blocked"
    assert blocked_bundle.fallback_gate_reason == "policy_diagnostic_only_requires_system_error_intent"
    assert blocked_bundle.fallback_used is False
    assert external_retriever.calls == []

    allowed_bundle = resolver.resolve(
        query="qsub command not found and scheduler failed",
        domain=TaskDomain.SYSTEM,
    )
    assert allowed_bundle.fallback_requested is True
    assert allowed_bundle.fallback_gate_decision == "allowed"
    assert allowed_bundle.fallback_gate_reason == "policy_diagnostic_only"
    assert allowed_bundle.fallback_used is True
    assert external_retriever.calls


def test_knowledge_resolver_disables_external_fallback_by_policy() -> None:
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
    resolver = KnowledgeResolver(
        local_retriever=local_retriever,
        external_retriever=external_retriever,
        external_fallback_enabled=False,
    )

    bundle = resolver.resolve(query="insufficient local coverage", domain=TaskDomain.KNOWLEDGE)

    assert bundle.fallback_requested is True
    assert bundle.fallback_gate_decision == "blocked"
    assert bundle.fallback_gate_reason == "external_fallback_disabled"
    assert bundle.fallback_used is False
    assert bundle.external_hits == []
    assert external_retriever.calls == []
    assert "fallback=blocked_by_gate" in bundle.rationale


def test_knowledge_resolver_emits_scheduler_diagnostic_suggestions() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="sbatch: command not found when submitting job to slurm",
        domain=TaskDomain.SYSTEM,
    )

    assert bundle.diagnostic_suggestions
    suggestion = next(
        item for item in bundle.diagnostic_suggestions if item.pattern_id == "slurm.command_not_found"
    )
    assert suggestion.tool == "slurm"
    assert suggestion.error_category == "command_not_found"
    assert any("which sbatch squeue sacct" in action for action in suggestion.suggested_actions)
    assert any("references/evaluation/diagnostics/scheduler_error_patterns.md" in source for source in suggestion.reference_sources)


def test_knowledge_resolver_emits_bio_tool_diagnostic_suggestions() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="bcftools could not load index for input.vcf.gz and failed to open .csi",
        domain=TaskDomain.BIOINFORMATICS,
    )

    assert bundle.diagnostic_suggestions
    suggestion = next(item for item in bundle.diagnostic_suggestions if item.tool == "bcftools")
    assert suggestion.pattern_id == "bcftools.index_missing"
    assert suggestion.error_category == "index_missing"
    assert any("bcftools index -f <input.vcf.gz>" in action for action in suggestion.suggested_actions)
    assert any("references/evaluation/diagnostics/bio_tool_error_patterns.md" in source for source in suggestion.reference_sources)


def test_knowledge_resolver_non_error_query_keeps_diagnostics_empty() -> None:
    resolver = KnowledgeResolver()

    bundle = resolver.resolve(
        query="summarize genomic prediction report template and validation workflow",
        domain=TaskDomain.BIOINFORMATICS,
    )

    assert bundle.diagnostic_suggestions == []


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
