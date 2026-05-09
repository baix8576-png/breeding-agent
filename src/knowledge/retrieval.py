"""Local-first retrieval services used by the orchestration runtime."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.common import TaskDomain
from knowledge.indexing import ReferenceKnowledgeIndexer

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_REFERENCES_ROOT = _PROJECT_ROOT / "references"
_ERROR_INTENT_TOKENS = (
    "error",
    "failed",
    "failure",
    "cannot",
    "can't",
    "not found",
    "no such file",
    "permission denied",
    "timed out",
    "timeout",
    "oom",
    "killed",
    "traceback",
    "\u62a5\u9519",
    "\u9519\u8bef",
    "\u5931\u8d25",
    "\u65e0\u6cd5",
    "\u627e\u4e0d\u5230",
    "\u8d85\u65f6",
)
_SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}
_SENSITIVITY_RANK = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "restricted": 4,
}
_DEFAULT_DOMAIN_SENSITIVITY_LIMITS = {
    TaskDomain.BIOINFORMATICS.value: "low",
    TaskDomain.KNOWLEDGE.value: "medium",
    TaskDomain.SYSTEM.value: "low",
}
_DATA_PATH_PATTERN = re.compile(
    r"([A-Za-z]:[\\/][^\\/\s]+(?:[\\/][^\\/\s]+)*\.(?:vcf(?:\.gz)?|bam|fastq(?:\.gz)?|fasta|fa|bed|bim|fam|ped|tsv|csv)|"
    r"/[^/\s]+(?:/[^/\s]+)*\.(?:vcf(?:\.gz)?|bam|fastq(?:\.gz)?|fasta|fa|bed|bim|fam|ped|tsv|csv))",
    flags=re.IGNORECASE,
)
_RESTRICTED_SENSITIVITY_TOKENS = (
    "password",
    "passwd",
    "secret",
    "client_secret",
    "private key",
    "ssh-rsa",
    "api_key",
    "access key",
    "refresh_token",
    "credential",
    "密码",
    "密钥",
    "令牌",
    "凭证",
)
_HIGH_SENSITIVITY_TOKENS = (
    "vcf",
    "bam",
    "fastq",
    "fasta",
    "plink",
    ".bed",
    ".bim",
    ".fam",
    "phenotype",
    "covariate",
    "pedigree",
    "sample_id",
    "iid",
    "fid",
    "表型",
    "协变量",
    "谱系",
    "样本",
)
_MEDIUM_SENSITIVITY_TOKENS = (
    "cohort",
    "study",
    "project",
    "internal",
    "审计",
    "日志",
)


@dataclass(frozen=True)
class _DiagnosticPattern:
    pattern_id: str
    tool: str
    error_category: str
    severity: str
    regex_signals: tuple[str, ...]
    tool_aliases: tuple[str, ...]
    suggested_actions: tuple[str, ...]
    reference_hints: tuple[str, ...] = ()


_DIAGNOSTIC_PATTERNS: tuple[_DiagnosticPattern, ...] = (
    _DiagnosticPattern(
        pattern_id="slurm.command_not_found",
        tool="slurm",
        error_category="command_not_found",
        severity="high",
        regex_signals=(
            r"(sbatch|squeue|sacct)\s*:\s*command not found",
            r"\u627e\u4e0d\u5230.*(sbatch|squeue|sacct)",
            r"slurm.*not found",
        ),
        tool_aliases=("slurm", "sbatch", "squeue", "sacct"),
        suggested_actions=(
            "Run `which sbatch squeue sacct` to confirm scheduler binaries are on PATH.",
            "Load scheduler runtime in login shell (for example `module load slurm`).",
            "Re-submit with an explicit command check: `bash -lc 'which sbatch && sbatch <job_script.sh>'`.",
        ),
        reference_hints=("scheduler", "slurm"),
    ),
    _DiagnosticPattern(
        pattern_id="slurm.invalid_partition",
        tool="slurm",
        error_category="queue_invalid",
        severity="high",
        regex_signals=(
            r"invalid partition",
            r"partition .* does not exist",
            r"invalid qos",
        ),
        tool_aliases=("slurm", "sbatch", "partition", "qos"),
        suggested_actions=(
            "Inspect available queues with `sinfo -s` (and QOS if enabled).",
            "Update job script to a valid queue, for example `#SBATCH -p <valid_partition>`.",
            "Dry-run submit command once: `sbatch --test-only <job_script.sh>`.",
        ),
        reference_hints=("scheduler", "partition", "queue"),
    ),
    _DiagnosticPattern(
        pattern_id="slurm.resource_oom",
        tool="slurm",
        error_category="resource_memory",
        severity="critical",
        regex_signals=(
            r"oom-kill",
            r"out of memory",
            r"exceeded memory limit",
            r"maxrss",
        ),
        tool_aliases=("slurm", "sbatch", "sacct"),
        suggested_actions=(
            "Profile the failed job with `sacct -j <job_id> --format=JobID,State,ReqMem,MaxRSS,Elapsed`.",
            "Increase memory request in script, for example `#SBATCH --mem=32G`.",
            "Reduce parallel pressure (threads/chunks) and rerun by chromosome or batch.",
        ),
        reference_hints=("scheduler", "resource", "memory"),
    ),
    _DiagnosticPattern(
        pattern_id="pbs.command_not_found",
        tool="pbs",
        error_category="command_not_found",
        severity="high",
        regex_signals=(
            r"(qsub|qstat)\s*:\s*command not found",
            r"\u627e\u4e0d\u5230.*(qsub|qstat)",
            r"pbs.*not found",
        ),
        tool_aliases=("pbs", "qsub", "qstat"),
        suggested_actions=(
            "Run `which qsub qstat` to verify PBS client installation.",
            "Load cluster module/environment for PBS (for example `module load pbs`).",
            "Re-run submit with a minimal script: `qsub <job_script.pbs>`.",
        ),
        reference_hints=("scheduler", "pbs"),
    ),
    _DiagnosticPattern(
        pattern_id="pbs.resource_invalid",
        tool="pbs",
        error_category="resource_request_invalid",
        severity="high",
        regex_signals=(
            r"unknown resource",
            r"illegal attribute or resource value",
            r"job exceeds queue resource limits",
        ),
        tool_aliases=("pbs", "qsub", "walltime", "select"),
        suggested_actions=(
            "Inspect queue limits with `qstat -Qf` and read `resources_max.*` fields.",
            "Submit with explicit resources, for example `qsub -l select=1:ncpus=8:mem=32gb -l walltime=12:00:00 <job_script.pbs>`.",
            "Align requested queue/resources in scheduler config with actual queue policy.",
        ),
        reference_hints=("scheduler", "pbs", "resource"),
    ),
    _DiagnosticPattern(
        pattern_id="plink2.input_missing",
        tool="plink2",
        error_category="input_missing",
        severity="high",
        regex_signals=(
            r"plink2.*(failed to open|cannot open|no such file)",
            r"error:.*(--bfile|--vcf).*not found",
            r"failed to open .*\.bed",
        ),
        tool_aliases=("plink2", "plink", "--bfile", "--vcf"),
        suggested_actions=(
            "Check genotype prefix files: `ls -lh <prefix>.bed <prefix>.bim <prefix>.fam`.",
            "If source is VCF, regenerate PLINK set: `plink2 --vcf <input.vcf.gz> --make-bed --out <prefix>`.",
            "Use absolute paths in wrapper/script and rerun from project workdir.",
        ),
        reference_hints=("input_specs", "plink", "qc"),
    ),
    _DiagnosticPattern(
        pattern_id="plink2.chromosome_format",
        tool="plink2",
        error_category="format_chromosome",
        severity="medium",
        regex_signals=(
            r"nonstandard chromosome",
            r"invalid chromosome code",
            r"--allow-extra-chr",
        ),
        tool_aliases=("plink2", "plink", "chromosome"),
        suggested_actions=(
            "Allow non-human chr names when needed: `plink2 --vcf <input.vcf.gz> --allow-extra-chr --make-bed --out <prefix>`.",
            "Normalize contig names before conversion (match species naming convention).",
            "Re-check input specification file for accepted chromosome labels.",
        ),
        reference_hints=("input_specs", "plink", "structure_analysis"),
    ),
    _DiagnosticPattern(
        pattern_id="bcftools.index_missing",
        tool="bcftools",
        error_category="index_missing",
        severity="high",
        regex_signals=(
            r"bcftools.*(could not load index|index.*not found)",
            r"failed to open .*\.csi",
            r"\[e::hts_open_format\]",
        ),
        tool_aliases=("bcftools", "tabix", "csi", "tbi"),
        suggested_actions=(
            "Compress and index VCF: `bgzip -f <input.vcf> && tabix -f -p vcf <input.vcf.gz>`.",
            "Rebuild index explicitly: `bcftools index -f <input.vcf.gz>`.",
            "Validate readable header: `bcftools view -h <input.vcf.gz> | head`.",
        ),
        reference_hints=("input_specs", "qc", "vcf"),
    ),
    _DiagnosticPattern(
        pattern_id="bcftools.vcf_format",
        tool="bcftools",
        error_category="vcf_format_invalid",
        severity="high",
        regex_signals=(
            r"bcftools.*(invalid|malformed).*vcf",
            r"contig.*not defined in the header",
            r"incorrect number of fields",
        ),
        tool_aliases=("bcftools", "vcf"),
        suggested_actions=(
            "Inspect and save current header: `bcftools view -h <input.vcf.gz> > header.txt`.",
            "Fix contig header using reference index: `bcftools reheader -f <ref.fa.fai> -o <fixed.vcf.gz> <input.vcf.gz>`.",
            "Normalize multi-allelic representation: `bcftools norm -m-any -Oz -o <normalized.vcf.gz> <fixed.vcf.gz>`.",
        ),
        reference_hints=("input_specs", "qc", "vcf"),
    ),
    _DiagnosticPattern(
        pattern_id="vcftools.input_open_failed",
        tool="vcftools",
        error_category="input_open_failed",
        severity="high",
        regex_signals=(
            r"vcftools.*(could not open|error).*vcf",
            r"can't determine file type",
            r"failed to open vcf file",
        ),
        tool_aliases=("vcftools", "vcf", "--gzvcf"),
        suggested_actions=(
            "Ensure compressed VCF input: `bgzip -f <input.vcf> && tabix -f -p vcf <input.vcf.gz>`.",
            "Use gz input flag explicitly: `vcftools --gzvcf <input.vcf.gz> --out <out_prefix> <options>`.",
            "Check path/permission inside job shell with `pwd` and `ls -lh <input.vcf.gz>`.",
        ),
        reference_hints=("input_specs", "qc", "vcf"),
    ),
    _DiagnosticPattern(
        pattern_id="gcta.grm_missing",
        tool="gcta",
        error_category="grm_or_plink_missing",
        severity="high",
        regex_signals=(
            r"gcta.*(cannot open|failed to open).*(grm|bed|bim|fam)",
            r"grm.*not found",
        ),
        tool_aliases=("gcta", "gcta64", "grm"),
        suggested_actions=(
            "Verify genotype prefix exists: `ls -lh <prefix>.bed <prefix>.bim <prefix>.fam`.",
            "Build GRM first: `gcta64 --bfile <prefix> --make-grm --out <grm_prefix>`.",
            "Then run model stage: `gcta64 --grm <grm_prefix> --reml --pheno <phenotype.tsv> --out <reml_out>`.",
        ),
        reference_hints=("genomic_prediction", "modeling_guides", "grm"),
    ),
    _DiagnosticPattern(
        pattern_id="gcta.id_mismatch",
        tool="gcta",
        error_category="sample_id_mismatch",
        severity="critical",
        regex_signals=(
            r"gcta.*(individual id|id mismatch|no individual found)",
            r"phenotype.*not found in",
            r"sample.*not found",
        ),
        tool_aliases=("gcta", "gcta64", "phenotype", "covariate"),
        suggested_actions=(
            "Preview IDs in phenotype/covariate: `cut -f1-2 <phenotype.tsv> | head` and `cut -f1-2 <covariate.tsv> | head`.",
            "Intersect sample IDs and rebuild aligned genotype set before modeling.",
            "Re-run with consistent FID/IID keys across PLINK, phenotype, and covariate files.",
        ),
        reference_hints=("input_specs", "genomic_prediction", "modeling_guides"),
    ),
)

_GENERIC_TOOL_RECOVERY: dict[str, dict[str, object]] = {
    "slurm": {
        "aliases": ("slurm", "sbatch", "squeue", "sacct"),
        "error_category": "generic_scheduler_error",
        "severity": "medium",
        "suggested_actions": (
            "Capture recent scheduler state: `squeue -j <job_id> -o '%i %T %r %M %D %C %m'`.",
            "Inspect failure log from submit script and run `sacct -j <job_id> --format=JobID,State,ExitCode,Elapsed`.",
            "Re-run dry-run generation and compare resource/partition values before re-submit.",
        ),
        "reference_hints": ("scheduler", "slurm"),
    },
    "pbs": {
        "aliases": ("pbs", "qsub", "qstat"),
        "error_category": "generic_scheduler_error",
        "severity": "medium",
        "suggested_actions": (
            "Inspect queue and job status: `qstat -f <job_id>` and `qstat -Qf`.",
            "Check stderr/stdout paths in PBS script and verify requested resources match queue policy.",
            "Re-submit after `qsub <job_script.pbs>` dry check in login shell.",
        ),
        "reference_hints": ("scheduler", "pbs"),
    },
    "plink2": {
        "aliases": ("plink2", "plink"),
        "error_category": "generic_tool_error",
        "severity": "medium",
        "suggested_actions": (
            "Run `plink2 --version` and confirm executable in PATH (`which plink2`).",
            "Validate core input bundle exists (`.bed/.bim/.fam` or `.vcf.gz`) before rerun.",
            "Re-run the exact command with `--out <debug_prefix>` and inspect generated `.log` first.",
        ),
        "reference_hints": ("input_specs", "qc", "plink"),
    },
    "bcftools": {
        "aliases": ("bcftools",),
        "error_category": "generic_tool_error",
        "severity": "medium",
        "suggested_actions": (
            "Run `bcftools --version` and validate command availability.",
            "Check input readability with `bcftools view -h <input.vcf.gz> | head`.",
            "If command fails in pipeline, execute the same command in isolation on a small region.",
        ),
        "reference_hints": ("input_specs", "qc", "vcf"),
    },
    "vcftools": {
        "aliases": ("vcftools",),
        "error_category": "generic_tool_error",
        "severity": "medium",
        "suggested_actions": (
            "Run `vcftools --version` and verify binary path.",
            "Confirm compressed/indexed input (`.vcf.gz` + `.tbi/.csi`) before command execution.",
            "Replay failing command with minimal options to isolate parameter-side failures.",
        ),
        "reference_hints": ("input_specs", "qc", "vcf"),
    },
    "gcta": {
        "aliases": ("gcta", "gcta64"),
        "error_category": "generic_tool_error",
        "severity": "medium",
        "suggested_actions": (
            "Run `gcta64 --version` (or `gcta --version`) and verify executable path.",
            "Validate required upstream outputs exist (PLINK set and GRM prefix) before model run.",
            "Re-run failing stage standalone and inspect `.log` plus phenotype/covariate headers.",
        ),
        "reference_hints": ("genomic_prediction", "modeling_guides", "grm"),
    },
}


class RetrievalDocument(BaseModel):
    """Small document abstraction shared by local and external retrieval."""

    source: str
    path: str = ""
    doc_id: str | None = None
    chunk_id: str | None = None
    section: str | None = None
    page_or_anchor: str | None = None
    blueprint_scope: str | None = None
    species: str | None = None
    evidence_level: str | None = None
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    retrieval_channels: list[str] = Field(default_factory=list)
    score: int = 0
    matched_tags: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    hit_reasons: list[str] = Field(default_factory=list)
    conflict_entries: list[str] = Field(default_factory=list)
    confidence_sources: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class DiagnosticSuggestion(BaseModel):
    """Structured, actionable diagnosis for common scheduler/tool failures."""

    pattern_id: str
    tool: str
    error_category: str
    severity: str
    matched_signals: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    reference_sources: list[str] = Field(default_factory=list)


class RetrievalBundle(BaseModel):
    """Stable retrieval output consumed by workflow planning."""

    query: str
    domain: TaskDomain
    local_hits: list[RetrievalDocument] = Field(default_factory=list)
    external_hits: list[RetrievalDocument] = Field(default_factory=list)
    fallback_requested: bool = False
    fallback_gate_decision: str = "not_requested"
    fallback_gate_reason: str = "coverage_high"
    fallback_gate_audit: dict[str, object] = Field(default_factory=dict)
    fallback_used: bool = False
    retrieval_mode: str = "local_only"
    coverage: str = "low"
    rationale: list[str] = Field(default_factory=list)
    evidence_conflicts: list[str] = Field(default_factory=list)
    confidence_sources: list[str] = Field(default_factory=list)
    diagnostic_suggestions: list[DiagnosticSuggestion] = Field(default_factory=list)

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
        documents.extend(self._chunk_documents_from_references())
        return documents

    def _chunk_documents_from_references(self) -> list[RetrievalDocument]:
        """Expose validated knowledge_item.v2 cards as traceable retrieval chunks."""

        load_result = ReferenceKnowledgeIndexer(_REFERENCES_ROOT).build()
        documents: list[RetrievalDocument] = []
        for chunk in load_result.chunks:
            documents.append(
                RetrievalDocument(
                    source="reference",
                    path=chunk.source_path,
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                    section=chunk.section,
                    page_or_anchor=chunk.page_or_anchor,
                    blueprint_scope=chunk.blueprint_scope.value,
                    species=chunk.species,
                    evidence_level=chunk.evidence_level.value,
                    title=chunk.section,
                    summary=self._truncate_summary(chunk.text),
                    tags=sorted(
                        dict.fromkeys(
                            [
                                "reference",
                                "shared",
                                TaskDomain.BIOINFORMATICS.value,
                                chunk.blueprint_scope.value,
                                chunk.evidence_level.value,
                                chunk.source.value,
                                chunk.species.lower(),
                                "knowledge_item_v2",
                            ]
                        )
                    ),
                    keywords=chunk.keywords,
                    retrieval_channels=["bm25", "keyword", "embedding_lite"],
                )
            )
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
    def _truncate_summary(text: str, limit: int = 360) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 3].rstrip() + "..."

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

    @staticmethod
    def _build_confidence_sources(
        *,
        score: int,
        token_count: int,
        matched_keywords: set[str],
        matched_tags: set[str],
        title_hits: set[str],
        summary_hits: set[str],
        path_hits: set[str],
        document: RetrievalDocument,
    ) -> list[str]:
        expected_max = max(token_count, 1) * 10
        score_ratio = round(score / expected_max, 3) if expected_max else 0.0
        keyword_bonus = 0.08 if matched_keywords else 0.0
        tag_bonus = 0.05 if matched_tags else 0.0
        title_bonus = 0.07 if title_hits else 0.0

        sources = [
            (
                "confidence_formula:min(1.0,score_ratio+keyword_bonus+tag_bonus+title_bonus)"
                f";score_ratio={score_ratio};keyword_bonus={keyword_bonus};"
                f"tag_bonus={tag_bonus};title_bonus={title_bonus}"
            )
        ]
        if matched_keywords:
            sources.append(f"matched_keywords:{','.join(sorted(matched_keywords)[:8])}")
        if matched_tags:
            sources.append(f"matched_tags:{','.join(sorted(matched_tags)[:8])}")
        if title_hits:
            sources.append(f"title_hits:{','.join(sorted(title_hits)[:8])}")
        if summary_hits:
            sources.append(f"summary_hits:{','.join(sorted(summary_hits)[:8])}")
        if path_hits:
            sources.append(f"path_hits:{','.join(sorted(path_hits)[:8])}")
        if document.retrieval_channels:
            sources.append(f"retrieval_channels:{','.join(document.retrieval_channels)}")
        if document.evidence_level:
            sources.append(f"evidence_level:{document.evidence_level}")
        if document.source:
            sources.append(f"source:{document.source}")
        return sources

    @staticmethod
    def _build_conflict_entries(
        *,
        document: RetrievalDocument,
        peers: list[RetrievalDocument],
    ) -> list[str]:
        conflicts: list[str] = []
        seen: set[str] = set()
        current_keywords = set(document.matched_keywords)
        current_tags = set(document.matched_tags)

        for peer in peers:
            if peer is document:
                continue
            shared_keywords = sorted(current_keywords.intersection(peer.matched_keywords))
            shared_tags = sorted(current_tags.intersection(peer.matched_tags))
            against = peer.doc_id or peer.title

            if (
                document.blueprint_scope
                and peer.blueprint_scope
                and document.blueprint_scope != peer.blueprint_scope
                and shared_keywords
            ):
                entry = (
                    "blueprint_scope_conflict:"
                    f"{document.blueprint_scope}!={peer.blueprint_scope};"
                    f"shared_keywords={','.join(shared_keywords[:6])};against={against}"
                )
                if entry not in seen:
                    seen.add(entry)
                    conflicts.append(entry)

            if (
                document.evidence_level
                and peer.evidence_level
                and document.evidence_level != peer.evidence_level
                and (document.doc_id == peer.doc_id or len(shared_keywords) >= 2)
            ):
                entry = (
                    "evidence_level_conflict:"
                    f"{document.evidence_level}!={peer.evidence_level};"
                    f"shared_keywords={','.join(shared_keywords[:6]) or 'none'};against={against}"
                )
                if entry not in seen:
                    seen.add(entry)
                    conflicts.append(entry)

            if (
                document.doc_id
                and peer.doc_id
                and document.doc_id == peer.doc_id
                and document.chunk_id
                and peer.chunk_id
                and document.chunk_id != peer.chunk_id
            ):
                entry = (
                    "intra_doc_focus_conflict:"
                    f"{document.chunk_id}!={peer.chunk_id};"
                    f"shared_tags={','.join(shared_tags[:6]) or 'none'}"
                )
                if entry not in seen:
                    seen.add(entry)
                    conflicts.append(entry)
        return conflicts[:6]

    def _attach_evidence_chain(self, hits: list[RetrievalDocument]) -> list[RetrievalDocument]:
        positive_hits = [item for item in hits if item.score > 0]
        if not positive_hits:
            return hits

        annotated: list[RetrievalDocument] = []
        for hit in hits:
            if hit.score <= 0:
                annotated.append(
                    hit.model_copy(
                        update={
                            "conflict_entries": [],
                            "confidence_sources": hit.confidence_sources or ["score:0"],
                        }
                    )
                )
                continue
            conflict_entries = self._build_conflict_entries(document=hit, peers=positive_hits)
            annotated.append(
                hit.model_copy(
                    update={
                        "conflict_entries": conflict_entries,
                    }
                )
            )
        return annotated

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
        if document.doc_id:
            hit_reasons.append(f"doc_id:{document.doc_id}")
        if document.chunk_id:
            hit_reasons.append(f"chunk_id:{document.chunk_id}")
        if document.evidence_level:
            hit_reasons.append(f"evidence_level:{document.evidence_level}")
        if document.page_or_anchor:
            hit_reasons.append(f"anchor:{document.page_or_anchor}")
        if document.retrieval_channels:
            hit_reasons.append(f"retrieval_channels:{','.join(document.retrieval_channels)}")
        confidence = self._confidence_from_score(
            score=score,
            token_count=len(query_tokens),
            matched_keywords=matched_keywords,
            matched_tags=matched_tags,
            title_hits=title_hits,
        )
        confidence_sources = self._build_confidence_sources(
            score=score,
            token_count=len(query_tokens),
            matched_keywords=matched_keywords,
            matched_tags=matched_tags,
            title_hits=title_hits,
            summary_hits=summary_hits,
            path_hits=path_hits,
            document=document,
        )
        return {
            "score": score,
            "matched_tags": sorted(matched_tags),
            "matched_keywords": sorted(matched_keywords),
            "hit_reasons": hit_reasons,
            "conflict_entries": [],
            "confidence_sources": confidence_sources,
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
            return self._attach_evidence_chain(top_hits)
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
                conflict_entries=[],
                confidence_sources=["fallback_local_primer", "confidence_not_model_based"],
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

    _VALID_POLICIES = {"always", "knowledge_only", "diagnostic_only", "tiered"}

    def __init__(
        self,
        *,
        enabled: bool = True,
        policy: str = "tiered",
        domain_sensitivity_limits: dict[str, str] | None = None,
        default_sensitivity: str = "low",
    ) -> None:
        self._enabled = enabled
        normalized_policy = policy.strip().lower() if policy else "tiered"
        if normalized_policy not in self._VALID_POLICIES:
            normalized_policy = "tiered"
        self._policy = normalized_policy
        self._default_sensitivity = self._normalize_sensitivity_level(default_sensitivity, fallback="low")
        self._domain_sensitivity_limits = self._normalize_domain_sensitivity_limits(
            domain_sensitivity_limits
        )

    @property
    def policy(self) -> str:
        return self._policy

    @property
    def domain_sensitivity_limits(self) -> dict[str, str]:
        return dict(self._domain_sensitivity_limits)

    @property
    def default_sensitivity(self) -> str:
        return self._default_sensitivity

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.lower().split())

    @staticmethod
    def _normalize_sensitivity_level(level: str | None, *, fallback: str) -> str:
        normalized = str(level or "").strip().lower()
        if normalized in _SENSITIVITY_RANK:
            return normalized
        return fallback

    @classmethod
    def _normalize_domain_sensitivity_limits(cls, raw: dict[str, str] | None) -> dict[str, str]:
        limits = dict(_DEFAULT_DOMAIN_SENSITIVITY_LIMITS)
        if not raw:
            return limits
        for domain_key, sensitivity in raw.items():
            normalized_domain = str(domain_key).strip().lower()
            if not normalized_domain:
                continue
            limits[normalized_domain] = cls._normalize_sensitivity_level(
                sensitivity,
                fallback=limits.get(normalized_domain, "low"),
            )
        return limits

    @staticmethod
    def _domain_key(domain: TaskDomain) -> str:
        return domain.value

    @staticmethod
    def _contains_any_token(normalized_text: str, tokens: tuple[str, ...]) -> tuple[bool, str | None]:
        for token in tokens:
            if token in normalized_text:
                return True, token
        return False, None

    def _classify_sensitivity(
        self,
        *,
        query: str,
        local_hits: list[RetrievalDocument],
    ) -> tuple[str, list[str]]:
        normalized_query = self._normalize_text(query)
        reasons: list[str] = []

        restricted_match, restricted_token = self._contains_any_token(
            normalized_query,
            _RESTRICTED_SENSITIVITY_TOKENS,
        )
        if restricted_match:
            if restricted_token is not None:
                reasons.append(f"restricted_token:{restricted_token}")
            return ("restricted", reasons)

        if _DATA_PATH_PATTERN.search(query):
            reasons.append("raw_data_path_detected")
            return ("high", reasons)

        high_match, high_token = self._contains_any_token(normalized_query, _HIGH_SENSITIVITY_TOKENS)
        if high_match:
            if high_token is not None:
                reasons.append(f"high_signal:{high_token}")
            return ("high", reasons)

        medium_match, medium_token = self._contains_any_token(
            normalized_query,
            _MEDIUM_SENSITIVITY_TOKENS,
        )
        if medium_match:
            if medium_token is not None:
                reasons.append(f"medium_signal:{medium_token}")
            return ("medium", reasons)

        if any(hit.path for hit in local_hits):
            reasons.append("local_reference_paths_present")

        reasons.append(f"default_sensitivity:{self._default_sensitivity}")
        return (self._default_sensitivity, reasons)

    def _domain_limit(self, domain: TaskDomain) -> str:
        domain_key = self._domain_key(domain)
        return self._domain_sensitivity_limits.get(
            domain_key,
            self._domain_sensitivity_limits.get("default", "low"),
        )

    def evaluate(
        self,
        *,
        query: str,
        domain: TaskDomain,
        coverage: str,
        local_hits: list[RetrievalDocument],
    ) -> tuple[str, str, dict[str, object]]:
        sensitivity_level, sensitivity_reasons = self._classify_sensitivity(
            query=query,
            local_hits=local_hits,
        )
        domain_limit = self._domain_limit(domain)
        domain_key = self._domain_key(domain)
        sensitivity_rank = _SENSITIVITY_RANK[sensitivity_level]
        domain_limit_rank = _SENSITIVITY_RANK[domain_limit]
        audit: dict[str, object] = {
            "policy": self._policy,
            "domain": domain_key,
            "coverage": coverage,
            "data_sensitivity_level": sensitivity_level,
            "data_sensitivity_reasons": sensitivity_reasons,
            "domain_max_sensitivity_level": domain_limit,
            "domain_max_sensitivity_rank": domain_limit_rank,
            "sensitivity_rank": sensitivity_rank,
            "enabled": self._enabled,
        }
        if not self._enabled:
            audit["decision"] = "blocked"
            audit["reason"] = "external_fallback_disabled"
            return ("blocked", "external_fallback_disabled", audit)
        if self._policy == "always":
            audit["decision"] = "allowed"
            audit["reason"] = "policy_always"
            return ("allowed", "policy_always", audit)
        if self._policy == "knowledge_only":
            if domain in {TaskDomain.KNOWLEDGE, TaskDomain.SYSTEM}:
                audit["decision"] = "allowed"
                audit["reason"] = "policy_knowledge_only"
                return ("allowed", "policy_knowledge_only", audit)
            audit["decision"] = "blocked"
            audit["reason"] = "policy_knowledge_only_blocks_domain"
            return ("blocked", "policy_knowledge_only_blocks_domain", audit)
        if self._policy == "diagnostic_only":
            normalized_query = self._normalize_text(query)
            has_error_intent = any(token in normalized_query for token in _ERROR_INTENT_TOKENS)
            audit["has_error_intent"] = has_error_intent
            if domain == TaskDomain.SYSTEM and has_error_intent:
                audit["decision"] = "allowed"
                audit["reason"] = "policy_diagnostic_only"
                return ("allowed", "policy_diagnostic_only", audit)
            audit["decision"] = "blocked"
            audit["reason"] = "policy_diagnostic_only_requires_system_error_intent"
            return ("blocked", "policy_diagnostic_only_requires_system_error_intent", audit)
        if self._policy == "tiered":
            if sensitivity_rank <= domain_limit_rank:
                audit["decision"] = "allowed"
                audit["reason"] = "policy_tiered_allowed"
                return ("allowed", "policy_tiered_allowed", audit)
            audit["decision"] = "blocked"
            audit["reason"] = "policy_tiered_blocks_sensitivity"
            return ("blocked", "policy_tiered_blocks_sensitivity", audit)

        audit["decision"] = "blocked"
        audit["reason"] = f"invalid_policy:{self._policy}"
        return ("blocked", f"invalid_policy:{self._policy}", audit)


class KnowledgeResolver:
    """Coordinate local-first retrieval with deterministic fallback behavior."""

    def __init__(
        self,
        local_retriever: LocalKnowledgeRetriever | None = None,
        external_retriever: ExternalKnowledgeRetriever | None = None,
        fallback_gate: ExternalFallbackGate | None = None,
        external_fallback_enabled: bool = True,
        external_fallback_policy: str = "tiered",
        external_fallback_domain_sensitivity_limits: dict[str, str] | None = None,
        external_fallback_default_sensitivity: str = "low",
    ) -> None:
        self._local_retriever = local_retriever or LocalKnowledgeRetriever()
        self._external_retriever = external_retriever or ExternalKnowledgeRetriever()
        self._external_fallback_enabled = external_fallback_enabled
        self._external_fallback_policy = external_fallback_policy
        self._fallback_gate = fallback_gate or ExternalFallbackGate(
            enabled=external_fallback_enabled,
            policy=external_fallback_policy,
            domain_sensitivity_limits=external_fallback_domain_sensitivity_limits,
            default_sensitivity=external_fallback_default_sensitivity,
        )

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.lower().split())

    @staticmethod
    def _has_error_intent(query: str) -> bool:
        normalized = KnowledgeResolver._normalize_text(query)
        return any(token in normalized for token in _ERROR_INTENT_TOKENS)

    @staticmethod
    def _document_blob(document: RetrievalDocument) -> str:
        return " ".join(
            [
                document.title,
                document.summary,
                document.path,
                " ".join(document.tags),
                " ".join(document.keywords),
            ]
        ).lower()

    @staticmethod
    def _reference_source_label(document: RetrievalDocument) -> str:
        if document.path:
            return f"{document.title} ({document.path})"
        return document.title

    @staticmethod
    def _unique_preserve_order(values: list[str], limit: int = 3) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique.append(normalized)
            if len(unique) >= limit:
                break
        return unique

    @staticmethod
    def _match_pattern_signals(query: str, pattern: _DiagnosticPattern) -> list[str]:
        matches: list[str] = []
        for signal in pattern.regex_signals:
            for match in re.finditer(signal, query, flags=re.IGNORECASE):
                snippet = match.group(0).strip()
                if snippet:
                    matches.append(snippet)
        return KnowledgeResolver._unique_preserve_order(matches, limit=6)

    @staticmethod
    def _tool_mentioned(query: str, tool_aliases: tuple[str, ...]) -> bool:
        return any(alias.lower() in query for alias in tool_aliases)

    def _collect_reference_sources(
        self,
        *,
        pattern: _DiagnosticPattern,
        domain: TaskDomain,
        query: str,
        local_hits: list[RetrievalDocument],
    ) -> list[str]:
        hints = tuple(
            dict.fromkeys(
                (
                    pattern.tool.lower(),
                    *pattern.tool_aliases,
                    *pattern.reference_hints,
                )
            )
        )

        def collect(documents: list[RetrievalDocument]) -> list[str]:
            prioritized: list[str] = []
            fallback: list[str] = []
            for document in documents:
                if document.source != "reference":
                    continue
                label = self._reference_source_label(document)
                fallback.append(label)
                blob = self._document_blob(document)
                if any(hint.lower() in blob for hint in hints):
                    prioritized.append(label)
            if prioritized:
                return self._unique_preserve_order(prioritized, limit=3)
            return self._unique_preserve_order(fallback, limit=3)

        local_refs = collect(local_hits)
        if local_refs:
            return local_refs

        probe_hits = self._local_retriever.search(
            query=f"{query} {pattern.tool} troubleshooting",
            domain=domain,
            limit=5,
        )
        return collect(probe_hits)

    def _build_diagnostic_suggestions(
        self,
        *,
        query: str,
        domain: TaskDomain,
        local_hits: list[RetrievalDocument],
    ) -> list[DiagnosticSuggestion]:
        normalized_query = self._normalize_text(query)
        if not normalized_query:
            return []

        suggestions: list[DiagnosticSuggestion] = []
        for pattern in _DIAGNOSTIC_PATTERNS:
            matched_signals = self._match_pattern_signals(normalized_query, pattern)
            if not matched_signals:
                continue
            reference_sources = self._collect_reference_sources(
                pattern=pattern,
                domain=domain,
                query=normalized_query,
                local_hits=local_hits,
            )
            suggestions.append(
                DiagnosticSuggestion(
                    pattern_id=pattern.pattern_id,
                    tool=pattern.tool,
                    error_category=pattern.error_category,
                    severity=pattern.severity,
                    matched_signals=matched_signals,
                    suggested_actions=list(pattern.suggested_actions),
                    reference_sources=reference_sources,
                )
            )

        has_error_intent = self._has_error_intent(normalized_query)
        if has_error_intent:
            known_tools = {suggestion.tool for suggestion in suggestions}
            for tool, config in _GENERIC_TOOL_RECOVERY.items():
                if tool in known_tools:
                    continue
                aliases = tuple(str(alias).lower() for alias in config["aliases"])
                if not self._tool_mentioned(normalized_query, aliases):
                    continue
                reference_hints = tuple(str(hint) for hint in config["reference_hints"])
                generic_pattern = _DiagnosticPattern(
                    pattern_id=f"{tool}.generic_error",
                    tool=tool,
                    error_category=str(config["error_category"]),
                    severity=str(config["severity"]),
                    regex_signals=(),
                    tool_aliases=aliases,
                    suggested_actions=tuple(str(action) for action in config["suggested_actions"]),
                    reference_hints=reference_hints,
                )
                reference_sources = self._collect_reference_sources(
                    pattern=generic_pattern,
                    domain=domain,
                    query=normalized_query,
                    local_hits=local_hits,
                )
                suggestions.append(
                    DiagnosticSuggestion(
                        pattern_id=f"{tool}.generic_error",
                        tool=tool,
                        error_category=str(config["error_category"]),
                        severity=str(config["severity"]),
                        matched_signals=[f"{tool}:error_intent"],
                        suggested_actions=[str(action) for action in config["suggested_actions"]],
                        reference_sources=reference_sources,
                    )
                )

        suggestions.sort(
            key=lambda item: (
                -_SEVERITY_RANK.get(item.severity, 0),
                item.tool,
                item.pattern_id,
            )
        )
        return suggestions[:8]

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
    ) -> tuple[str, str, dict[str, object]]:
        if not fallback_requested:
            return (
                "not_requested",
                "coverage_high",
                {
                    "policy": self._external_fallback_policy,
                    "enabled": self._external_fallback_enabled,
                    "domain": domain.value,
                    "coverage": coverage,
                    "decision": "not_requested",
                    "reason": "coverage_high",
                },
            )
        gate_response = self._fallback_gate.evaluate(
            query=query,
            domain=domain,
            coverage=coverage,
            local_hits=local_hits,
        )
        audit: dict[str, object] = {}
        if isinstance(gate_response, tuple):
            decision_raw = gate_response[0] if len(gate_response) > 0 else "blocked"
            reason_raw = gate_response[1] if len(gate_response) > 1 else "gate_blocked"
            if len(gate_response) > 2 and isinstance(gate_response[2], dict):
                audit = dict(gate_response[2])
        elif isinstance(gate_response, dict):
            decision_raw = gate_response.get("decision", "blocked")
            reason_raw = gate_response.get("reason", "gate_blocked")
            audit = dict(gate_response)
            audit.pop("decision", None)
            audit.pop("reason", None)
        else:
            decision_raw = gate_response
            reason_raw = "gate_allowed" if str(decision_raw).strip().lower() == "allowed" else "gate_blocked"
        decision = str(decision_raw).strip().lower()
        reason = str(reason_raw).strip() or "gate_blocked"
        audit.setdefault("policy", self._external_fallback_policy)
        audit.setdefault("enabled", self._external_fallback_enabled)
        audit.setdefault("domain", domain.value)
        audit.setdefault("coverage", coverage)
        audit["decision"] = decision
        audit["reason"] = reason
        if decision == "allowed":
            return ("allowed", reason if reason != "gate_blocked" else "gate_allowed", audit)
        if decision == "blocked":
            return ("blocked", reason if reason != "gate_allowed" else "gate_blocked", audit)
        audit["decision"] = "blocked"
        audit["reason"] = f"invalid_gate_decision:{decision}"
        return ("blocked", f"invalid_gate_decision:{decision}", audit)

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

    @staticmethod
    def _aggregate_evidence_conflicts(documents: list[RetrievalDocument], limit: int = 12) -> list[str]:
        conflicts: list[str] = []
        seen: set[str] = set()
        for document in documents:
            for entry in document.conflict_entries:
                normalized = entry.strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                conflicts.append(normalized)
                if len(conflicts) >= limit:
                    return conflicts
        return conflicts

    @staticmethod
    def _aggregate_confidence_sources(documents: list[RetrievalDocument], limit: int = 16) -> list[str]:
        sources: list[str] = []
        seen: set[str] = set()
        for document in documents:
            for entry in document.confidence_sources:
                normalized = entry.strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                sources.append(normalized)
                if len(sources) >= limit:
                    return sources
        return sources

    def resolve(self, query: str, domain: TaskDomain) -> RetrievalBundle:
        """Resolve retrieval context using local sources first and external fallback second."""

        local_hits = self._local_retriever.search(query=query, domain=domain)
        diagnostic_suggestions = self._build_diagnostic_suggestions(
            query=query,
            domain=domain,
            local_hits=local_hits,
        )
        positive_hits = [document for document in local_hits if document.score > 0]
        top_score = max((document.score for document in positive_hits), default=0)
        coverage = "high" if len(positive_hits) >= 2 or top_score >= 5 else "partial" if len(positive_hits) == 1 else "low"
        fallback_requested = self._is_external_fallback_requested(coverage)
        fallback_gate_decision, fallback_gate_reason, fallback_gate_audit = self._decide_external_fallback(
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
        evidence_conflicts = self._aggregate_evidence_conflicts(local_hits)
        confidence_sources = self._aggregate_confidence_sources(local_hits)
        rationale = [
            f"local_hits={len(local_hits)}",
            f"positive_local_hits={len(positive_hits)}",
            f"top_local_score={top_score}",
            f"coverage={coverage}",
            f"fallback_requested={str(fallback_requested).lower()}",
            f"fallback_gate_decision={fallback_gate_decision}",
            f"fallback_gate_reason={fallback_gate_reason}",
            f"fallback_policy={self._external_fallback_policy}",
            f"fallback_data_sensitivity={fallback_gate_audit.get('data_sensitivity_level', 'n/a')}",
            f"fallback_domain_limit={fallback_gate_audit.get('domain_max_sensitivity_level', 'n/a')}",
            f"diagnostic_suggestions={len(diagnostic_suggestions)}",
            f"evidence_conflicts={len(evidence_conflicts)}",
            f"confidence_sources={len(confidence_sources)}",
        ]
        if diagnostic_suggestions:
            diagnostic_tools = ",".join(sorted({item.tool for item in diagnostic_suggestions}))
            rationale.append(f"diagnostic_tools={diagnostic_tools}")
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
            fallback_gate_audit=fallback_gate_audit,
            fallback_used=fallback_used,
            retrieval_mode="local_plus_external_fallback" if fallback_used else "local_only",
            coverage=coverage,
            rationale=rationale,
            evidence_conflicts=evidence_conflicts,
            confidence_sources=confidence_sources,
            diagnostic_suggestions=diagnostic_suggestions,
        )
