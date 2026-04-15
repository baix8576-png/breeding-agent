"""Local-first retrieval services used by the orchestration skeleton."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain


class RetrievalDocument(BaseModel):
    """Small document abstraction shared by local and external retrieval."""

    source: str
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    score: int = 0


class RetrievalBundle(BaseModel):
    """Stable retrieval output consumed by workflow planning."""

    query: str
    domain: TaskDomain
    local_hits: list[RetrievalDocument] = Field(default_factory=list)
    external_hits: list[RetrievalDocument] = Field(default_factory=list)
    fallback_used: bool = False
    retrieval_mode: str = "local_only"
    coverage: str = "low"
    rationale: list[str] = Field(default_factory=list)

    @property
    def source_labels(self) -> list[str]:
        """Return retrieval source titles in a stable order."""

        labels = [document.title for document in self.local_hits]
        labels.extend(document.title for document in self.external_hits)
        return labels


class LocalKnowledgeRetriever:
    """Local retriever backed by a small in-repo starter catalog."""

    def __init__(self) -> None:
        self._catalog = [
            RetrievalDocument(
                source="local",
                title="Input Compliance Checklist",
                summary="Validate VCF/BAM/PLINK, phenotype, covariate, and pedigree inputs before planning.",
                tags=["shared", TaskDomain.BIOINFORMATICS.value],
                keywords=[
                    "vcf",
                    "bam",
                    "plink",
                    "phenotype",
                    "covariate",
                    "pedigree",
                    "\u8868\u578b",
                    "\u534f\u53d8\u91cf",
                    "\u8c31\u7cfb",
                    "\u8d28\u63a7",
                    "qc",
                ],
            ),
            RetrievalDocument(
                source="local",
                title="Population Structure Workflow",
                summary="Use PCA and structure analysis early to control stratification before downstream inference.",
                tags=[TaskDomain.BIOINFORMATICS.value],
                keywords=[
                    "pca",
                    "structure",
                    "admixture",
                    "fst",
                    "ld",
                    "roh",
                    "\u7fa4\u4f53\u7ed3\u6784",
                    "\u4e3b\u6210\u5206",
                    "\u5206\u5c42",
                    "\u4eb2\u7f18",
                ],
            ),
            RetrievalDocument(
                source="local",
                title="Quantitative Genetics Modeling Notes",
                summary="Draft GBLUP, ssGBLUP, Bayes-style, and validation choices without claiming final scientific conclusions.",
                tags=[TaskDomain.BIOINFORMATICS.value],
                keywords=[
                    "gblup",
                    "ssgblup",
                    "bayes",
                    "heritability",
                    "genomic selection",
                    "breeding value",
                    "\u9057\u4f20\u529b",
                    "\u57fa\u56e0\u7ec4\u9009\u62e9",
                    "\u80b2\u79cd\u503c",
                    "\u6570\u91cf\u9057\u4f20",
                ],
            ),
            RetrievalDocument(
                source="local",
                title="Scheduler and Resource Guardrails",
                summary="Estimate conservative CPU, memory, walltime, and partition values before dry-run submission.",
                tags=["shared", TaskDomain.BIOINFORMATICS.value, TaskDomain.SYSTEM.value],
                keywords=[
                    "slurm",
                    "pbs",
                    "scheduler",
                    "queue",
                    "resource",
                    "memory",
                    "thread",
                    "\u96c6\u7fa4",
                    "\u961f\u5217",
                    "\u8d44\u6e90",
                    "\u5185\u5b58",
                    "\u7ebf\u7a0b",
                ],
            ),
            RetrievalDocument(
                source="local",
                title="Safety and Redaction Policy",
                summary="Only prompts, sanitized logs, tool summaries, software versions, and parameter structure may leave the cluster.",
                tags=["shared", TaskDomain.SYSTEM.value, TaskDomain.KNOWLEDGE.value],
                keywords=[
                    "error",
                    "log",
                    "redaction",
                    "sanitize",
                    "api",
                    "upload",
                    "\u62a5\u9519",
                    "\u65e5\u5fd7",
                    "\u8131\u654f",
                    "\u4e0a\u4f20",
                    "\u9690\u79c1",
                ],
            ),
            RetrievalDocument(
                source="local",
                title="Knowledge Response Playbook",
                summary="Prefer local SOP, FAQ, and literature index summaries before external lookup placeholders.",
                tags=["shared", TaskDomain.KNOWLEDGE.value],
                keywords=[
                    "faq",
                    "sop",
                    "paper",
                    "literature",
                    "method",
                    "workflow",
                    "\u6587\u732e",
                    "\u65b9\u6cd5",
                    "\u6d41\u7a0b",
                    "\u77e5\u8bc6\u5e93",
                ],
            ),
        ]

    def search(
        self,
        query: str,
        domain: TaskDomain,
        limit: int = 3,
    ) -> list[RetrievalDocument]:
        """Return the top matching local knowledge entries."""

        normalized = query.lower()
        matches: list[RetrievalDocument] = []
        for document in self._catalog:
            if domain.value not in document.tags and "shared" not in document.tags:
                continue
            score = sum(1 for keyword in document.keywords if keyword in normalized)
            if score == 0 and domain.value not in document.tags and "shared" not in document.tags:
                continue
            matches.append(document.model_copy(update={"score": score}))

        matches.sort(key=lambda item: (-item.score, item.title))
        top_hits = matches[:limit]
        if top_hits:
            return top_hits
        return [
            RetrievalDocument(
                source="local",
                title=f"{domain.value.title()} Local Primer",
                summary=f"Starter local guidance for planning query: {query}",
                tags=["shared", domain.value],
                score=0,
            )
        ]


class ExternalKnowledgeRetriever:
    """Placeholder external retriever used only after local coverage is insufficient."""

    def search(self, query: str, domain: TaskDomain) -> list[RetrievalDocument]:
        """Return deterministic external placeholder hits without real network access."""

        if domain == TaskDomain.BIOINFORMATICS:
            return [
                RetrievalDocument(
                    source="external-placeholder",
                    title="External Method Index Placeholder",
                    summary="Attach MCP-backed method or literature retrieval here once local coverage is insufficient.",
                ),
                RetrievalDocument(
                    source="external-placeholder",
                    title="External Validation Reference Placeholder",
                    summary="Attach benchmark references here after sanitization rules pass.",
                ),
            ]
        if domain == TaskDomain.SYSTEM:
            return [
                RetrievalDocument(
                    source="external-placeholder",
                    title="External Diagnostic Knowledge Placeholder",
                    summary="Attach documentation or troubleshooting lookup here after log sanitization.",
                )
            ]
        return [
            RetrievalDocument(
                source="external-placeholder",
                title="External FAQ/Literature Placeholder",
                summary="Attach external background lookup here only after local SOP and FAQ sources are exhausted.",
            )
        ]


class KnowledgeResolver:
    """Coordinate local-first retrieval with deterministic fallback behavior."""

    def __init__(
        self,
        local_retriever: LocalKnowledgeRetriever | None = None,
        external_retriever: ExternalKnowledgeRetriever | None = None,
    ) -> None:
        self._local_retriever = local_retriever or LocalKnowledgeRetriever()
        self._external_retriever = external_retriever or ExternalKnowledgeRetriever()

    def resolve(self, query: str, domain: TaskDomain) -> RetrievalBundle:
        """Resolve retrieval context using local sources first and external placeholders second."""

        local_hits = self._local_retriever.search(query=query, domain=domain)
        positive_hits = [document for document in local_hits if document.score > 0]
        coverage = "high" if len(positive_hits) >= 2 else "partial" if len(positive_hits) == 1 else "low"
        fallback_used = coverage != "high"
        external_hits = self._external_retriever.search(query=query, domain=domain) if fallback_used else []
        rationale = [
            f"local_hits={len(local_hits)}",
            f"positive_local_hits={len(positive_hits)}",
            f"coverage={coverage}",
        ]
        if fallback_used:
            rationale.append("fallback=external_placeholder")

        return RetrievalBundle(
            query=query,
            domain=domain,
            local_hits=local_hits,
            external_hits=external_hits,
            fallback_used=fallback_used,
            retrieval_mode="local_plus_external_placeholder" if fallback_used else "local_only",
            coverage=coverage,
            rationale=rationale,
        )