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
    matched_tags: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    hit_reasons: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class RetrievalBundle(BaseModel):
    """Stable retrieval output consumed by workflow planning."""

    query: str
    domain: TaskDomain
    local_hits: list[RetrievalDocument] = Field(default_factory=list)
    external_hits: list[RetrievalDocument] = Field(default_factory=list)
    fallback_requested: bool = False
    fallback_gate_decision: str = "not_requested"
    fallback_gate_reason: str = "coverage_high"
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

    @staticmethod
    def _query_tokens(query: str) -> list[str]:
        return [token.lower() for token in _TOKEN_PATTERN.findall(query.lower())]

    @staticmethod
    def _build_hit_reasons(
        *,
        title_hits: set[str],
        summary_hits: set[str],
        path_hits: set[str],
        matched_keywords: set[str],
        matched_tags: set[str],
    ) -> list[str]:
        reasons: list[str] = []
        if matched_keywords:
            reasons.append(f"keyword_match:{','.join(sorted(matched_keywords)[:8])}")
        if matched_tags:
            reasons.append(f"tag_match:{','.join(sorted(matched_tags)[:8])}")
        if title_hits:
            reasons.append(f"title_overlap:{','.join(sorted(title_hits)[:8])}")
        if summary_hits:
            reasons.append(f"summary_overlap:{','.join(sorted(summary_hits)[:8])}")
        if path_hits:
            reasons.append(f"path_overlap:{','.join(sorted(path_hits)[:8])}")
        if not reasons:
            reasons.append("no_direct_token_match")
        return reasons

    @staticmethod
    def _confidence_from_score(
        *,
        score: int,
        token_count: int,
        matched_keywords: set[str],
        matched_tags: set[str],
        title_hits: set[str],
    ) -> float:
        if score <= 0:
            return 0.0
        expected_max = max(token_count, 1) * 10
        confidence = score / expected_max
        if matched_keywords:
            confidence += 0.08
        if matched_tags:
            confidence += 0.05
        if title_hits:
            confidence += 0.07
        return round(min(1.0, confidence), 3)

    def _evaluate_document(self, query: str, document: RetrievalDocument) -> dict[str, object]:
        normalized = query.lower()
        score = 0
        query_tokens = self._query_tokens(normalized)
        title_lower = document.title.lower()
        summary_lower = document.summary.lower()
        path_lower = document.path.lower()
        keyword_tokens = [keyword.lower() for keyword in document.keywords]
        tag_tokens = [tag.lower() for tag in document.tags]
        matched_keywords: set[str] = set()
        matched_tags: set[str] = set()
        title_hits: set[str] = set()
        summary_hits: set[str] = set()
        path_hits: set[str] = set()
        for token in query_tokens:
            if token in title_lower:
                score += 3
                title_hits.add(token)
            if token in summary_lower:
                score += 2
                summary_hits.add(token)
            if token in path_lower:
                score += 2
                path_hits.add(token)
            if token in keyword_tokens:
                score += 2
                matched_keywords.add(token)
            elif any(token == keyword or token in keyword for keyword in keyword_tokens):
                score += 1
                matched_keywords.add(token)
            if token in tag_tokens:
                score += 1
                matched_tags.add(token)
        hit_reasons = self._build_hit_reasons(
            title_hits=title_hits,
            summary_hits=summary_hits,
            path_hits=path_hits,
            matched_keywords=matched_keywords,
            matched_tags=matched_tags,
        )
        confidence = self._confidence_from_score(
            score=score,
            token_count=len(query_tokens),
            matched_keywords=matched_keywords,
            matched_tags=matched_tags,
            title_hits=title_hits,
        )
        return {
            "score": score,
            "matched_tags": sorted(matched_tags),
            "matched_keywords": sorted(matched_keywords),
            "hit_reasons": hit_reasons,
            "confidence": confidence,
        }

    def _score_document(self, query: str, document: RetrievalDocument) -> int:
        return int(self._evaluate_document(query=query, document=document)["score"])

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
            evaluation = self._evaluate_document(query=query, document=document)
            matches.append(document.model_copy(update=evaluation))

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
                matched_tags=[domain.value],
                matched_keywords=self._query_tokens(query)[:6],
                hit_reasons=["fallback_local_primer", "local_catalog_no_positive_hits"],
                confidence=0.0,
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


class ExternalFallbackGate:
    """Gate external fallback so local-first retrieval remains the default behavior."""

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = enabled

    def evaluate(
        self,
        *,
        query: str,
        domain: TaskDomain,
        coverage: str,
        local_hits: list[RetrievalDocument],
    ) -> str:
        del query, domain, coverage, local_hits
        return "allowed" if self._enabled else "blocked"


class KnowledgeResolver:
    """Coordinate local-first retrieval with deterministic fallback behavior."""

    def __init__(
        self,
        local_retriever: LocalKnowledgeRetriever | None = None,
        external_retriever: ExternalKnowledgeRetriever | None = None,
        fallback_gate: ExternalFallbackGate | None = None,
        external_fallback_enabled: bool = True,
    ) -> None:
        self._local_retriever = local_retriever or LocalKnowledgeRetriever()
        self._external_retriever = external_retriever or ExternalKnowledgeRetriever()
        self._external_fallback_enabled = external_fallback_enabled
        self._fallback_gate = fallback_gate or ExternalFallbackGate(enabled=external_fallback_enabled)

    @staticmethod
    def _is_external_fallback_requested(coverage: str) -> bool:
        return coverage != "high"

    def _decide_external_fallback(
        self,
        *,
        query: str,
        fallback_requested: bool,
        local_hits: list[RetrievalDocument],
        coverage: str,
        domain: TaskDomain,
    ) -> tuple[str, str]:
        if not fallback_requested:
            return ("not_requested", "coverage_high")
        if not self._external_fallback_enabled:
            return ("blocked", "external_fallback_disabled")
        decision = self._fallback_gate.evaluate(
            query=query,
            domain=domain,
            coverage=coverage,
            local_hits=local_hits,
        )
        if decision == "allowed":
            return ("allowed", "gate_allowed")
        if decision == "blocked":
            return ("blocked", "gate_blocked")
        return ("blocked", f"invalid_gate_decision:{decision}")

    def _execute_external_fallback(
        self,
        *,
        query: str,
        domain: TaskDomain,
        fallback_requested: bool,
        fallback_gate_decision: str,
    ) -> tuple[bool, list[RetrievalDocument]]:
        if not fallback_requested or fallback_gate_decision != "allowed":
            return (False, [])
        external_hits = self._external_retriever.search(query=query, domain=domain)
        return (True, external_hits)

    def resolve(self, query: str, domain: TaskDomain) -> RetrievalBundle:
        """Resolve retrieval context using local sources first and external fallback second."""

        local_hits = self._local_retriever.search(query=query, domain=domain)
        positive_hits = [document for document in local_hits if document.score > 0]
        top_score = max((document.score for document in positive_hits), default=0)
        coverage = "high" if len(positive_hits) >= 2 or top_score >= 5 else "partial" if len(positive_hits) == 1 else "low"
        fallback_requested = self._is_external_fallback_requested(coverage)
        fallback_gate_decision, fallback_gate_reason = self._decide_external_fallback(
            query=query,
            fallback_requested=fallback_requested,
            local_hits=local_hits,
            coverage=coverage,
            domain=domain,
        )
        fallback_used, external_hits = self._execute_external_fallback(
            query=query,
            domain=domain,
            fallback_requested=fallback_requested,
            fallback_gate_decision=fallback_gate_decision,
        )
        rationale = [
            f"local_hits={len(local_hits)}",
            f"positive_local_hits={len(positive_hits)}",
            f"top_local_score={top_score}",
            f"coverage={coverage}",
            f"fallback_requested={str(fallback_requested).lower()}",
            f"fallback_gate_decision={fallback_gate_decision}",
            f"fallback_gate_reason={fallback_gate_reason}",
        ]
        if fallback_used:
            rationale.append("fallback=external_fallback")
        elif fallback_requested:
            rationale.append("fallback=blocked_by_gate")

        return RetrievalBundle(
            query=query,
            domain=domain,
            local_hits=local_hits,
            external_hits=external_hits,
            fallback_requested=fallback_requested,
            fallback_gate_decision=fallback_gate_decision,
            fallback_gate_reason=fallback_gate_reason,
            fallback_used=fallback_used,
            retrieval_mode="local_plus_external_fallback" if fallback_used else "local_only",
            coverage=coverage,
            rationale=rationale,
        )
