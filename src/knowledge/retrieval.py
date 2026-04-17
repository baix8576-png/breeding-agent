"""Local-first retrieval services used by the orchestration runtime."""

from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.common import TaskDomain

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REFERENCES_ROOT = _PROJECT_ROOT / "references"


class RetrievalDocument(BaseModel):
    """Small document abstraction shared by local and external retrieval."""

    source: str
    path: str = ""
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
    """Local retriever backed by project references and a starter catalog."""

    def __init__(self) -> None:
        self._catalog = self._load_catalog()

    def _load_catalog(self) -> list[RetrievalDocument]:
        """Load local reference assets and merge them with starter knowledge."""

        return self._load_reference_assets() + self._starter_catalog()

    def _starter_catalog(self) -> list[RetrievalDocument]:
        """Return deterministic starter knowledge entries."""

        return [
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
                summary="Prefer local SOP, FAQ, and literature index summaries before external fallback lookup.",
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

    def _load_reference_assets(self) -> list[RetrievalDocument]:
        """Scan references/* and turn markdown files into searchable assets."""

        if not _REFERENCES_ROOT.exists():
            return []

        documents: list[RetrievalDocument] = []
        for path in sorted(_REFERENCES_ROOT.rglob("*.md")):
            if not path.is_file():
                continue
            documents.append(self._document_from_reference(path))
        return documents

    def _document_from_reference(self, path: Path) -> RetrievalDocument:
        """Build a retrieval document from a markdown reference file."""

        text = self._read_text(path)
        title = self._extract_title(text, path)
        summary = self._extract_summary(text, title)
        tags = self._tags_from_path(path)
        keywords = self._keywords_from_text(title, summary, text, tags, path)
        return RetrievalDocument(
            source="reference",
            path=str(path.relative_to(_PROJECT_ROOT)).replace("\\", "/"),
            title=title,
            summary=summary,
            tags=tags,
            keywords=keywords,
        )

    @staticmethod
    def _read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _extract_title(text: str, path: Path) -> str:
        for line in text.splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                if title:
                    return title
        if path.name.lower() == "readme.md":
            return path.parent.name.replace("_", " ").title()
        return path.stem.replace("-", " ").replace("_", " ").title()

    @staticmethod
    def _extract_summary(text: str, title: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        summary_lines: list[str] = []
        seen_heading = False
        for line in lines:
            if not line:
                if seen_heading and summary_lines:
                    break
                continue
            if line.startswith("#"):
                seen_heading = True
                continue
            if line.startswith("- ") or line.startswith("`"):
                summary_lines.append(line.lstrip("- ").strip())
                if len(" ".join(summary_lines)) > 180:
                    break
                continue
            summary_lines.append(line)
            if len(" ".join(summary_lines)) > 180:
                break
        if summary_lines:
            return " ".join(summary_lines)
        return f"Reference material for {title}"

    @staticmethod
    def _tags_from_path(path: Path) -> list[str]:
        parts = list(path.relative_to(_REFERENCES_ROOT).parts)
        tags = ["reference", "shared"]
        if len(parts) > 1:
            tags.extend(part.replace("-", "_") for part in parts[:-1])
        else:
            tags.append(path.parent.name.replace("-", "_"))
        if path.name.lower() == "readme.md":
            tags.append(path.parent.name.replace("-", "_"))
        else:
            tags.append(path.stem.replace("-", "_").replace(".", "_"))
        return sorted(dict.fromkeys(tag for tag in tags if tag))

    @staticmethod
    def _keywords_from_text(*parts: object) -> list[str]:
        tokens: list[str] = []
        for part in parts:
            if isinstance(part, (str, Path)):
                tokens.extend(token.lower() for token in _TOKEN_PATTERN.findall(str(part)))
            else:
                for item in part:
                    tokens.extend(token.lower() for token in _TOKEN_PATTERN.findall(item))
        return list(dict.fromkeys(tokens))

    def _score_document(self, query: str, document: RetrievalDocument) -> int:
        normalized = query.lower()
        score = 0
        query_tokens = _TOKEN_PATTERN.findall(normalized)
        for token in query_tokens:
            if token in document.title.lower():
                score += 3
            if token in document.summary.lower():
                score += 2
            if token in document.path.lower():
                score += 2
            if token in document.keywords:
                score += 2
            elif any(token == keyword or token in keyword for keyword in document.keywords):
                score += 1
            if token in document.tags:
                score += 1
        return score

    def search(
        self,
        query: str,
        domain: TaskDomain,
        limit: int = 3,
    ) -> list[RetrievalDocument]:
        """Return the top matching local knowledge entries."""

        matches: list[RetrievalDocument] = []
        for document in self._catalog:
            if domain.value not in document.tags and "shared" not in document.tags:
                continue
            score = self._score_document(query=query, document=document)
            matches.append(document.model_copy(update={"score": score}))

        matches.sort(key=lambda item: (-item.score, item.title))
        top_hits = matches[:limit]
        positive_hits = [document for document in top_hits if document.score > 0]
        if positive_hits:
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
    """External fallback retriever used only after local coverage is insufficient."""

    def search(self, query: str, domain: TaskDomain) -> list[RetrievalDocument]:
        """Return deterministic external fallback hits without real network access."""

        if domain == TaskDomain.BIOINFORMATICS:
            return [
                RetrievalDocument(
                    source="external-fallback",
                    title="External Method Index Fallback",
                    summary="Attach MCP-backed method or literature retrieval here once local coverage is insufficient.",
                ),
                RetrievalDocument(
                    source="external-fallback",
                    title="External Validation Reference Fallback",
                    summary="Attach benchmark references here after sanitization rules pass.",
                ),
            ]
        if domain == TaskDomain.SYSTEM:
            return [
                RetrievalDocument(
                    source="external-fallback",
                    title="External Diagnostic Knowledge Fallback",
                    summary="Attach documentation or troubleshooting lookup here after log sanitization.",
                )
            ]
        return [
            RetrievalDocument(
                source="external-fallback",
                title="External FAQ/Literature Fallback",
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
        """Resolve retrieval context using local sources first and external fallback second."""

        local_hits = self._local_retriever.search(query=query, domain=domain)
        positive_hits = [document for document in local_hits if document.score > 0]
        top_score = max((document.score for document in positive_hits), default=0)
        coverage = "high" if len(positive_hits) >= 2 or top_score >= 5 else "partial" if len(positive_hits) == 1 else "low"
        fallback_used = coverage != "high"
        external_hits = self._external_retriever.search(query=query, domain=domain) if fallback_used else []
        rationale = [
            f"local_hits={len(local_hits)}",
            f"positive_local_hits={len(positive_hits)}",
            f"top_local_score={top_score}",
            f"coverage={coverage}",
        ]
        if fallback_used:
            rationale.append("fallback=external_fallback")

        return RetrievalBundle(
            query=query,
            domain=domain,
            local_hits=local_hits,
            external_hits=external_hits,
            fallback_used=fallback_used,
            retrieval_mode="local_plus_external_fallback" if fallback_used else "local_only",
            coverage=coverage,
            rationale=rationale,
        )
