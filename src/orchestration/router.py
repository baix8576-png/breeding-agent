"""Intent routing helpers for user requests."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain


class IntentClassification(BaseModel):
    """Structured request classification used by workflow planning."""

    domain: TaskDomain
    matched_keywords: list[str] = Field(default_factory=list)
    analysis_targets: list[str] = Field(default_factory=list)
    risk_hints: list[str] = Field(default_factory=list)
    requires_retrieval: bool = True


class IntentRouter:
    """Heuristic request router used until the real LLM workflow is added."""

    _bioinformatics_keywords = {
        "vcf",
        "bam",
        "plink",
        "pca",
        "gwas",
        "fst",
        "roh",
        "ld",
        "heritability",
        "gblup",
        "ssgblup",
        "bayes",
        "genomic selection",
        "breeding value",
        "\u7fa4\u4f53\u7ed3\u6784",
        "\u4e3b\u6210\u5206",
        "\u9057\u4f20\u529b",
        "\u57fa\u56e0\u7ec4\u9009\u62e9",
        "\u80b2\u79cd\u503c",
        "\u6570\u91cf\u9057\u4f20",
        "\u4eb2\u7f18",
    }
    _system_keywords = {
        "error",
        "log",
        "traceback",
        "failed",
        "why",
        "debug",
        "\u62a5\u9519",
        "\u65e5\u5fd7",
        "\u5931\u8d25",
        "\u8c03\u8bd5",
    }
    _analysis_targets = {
        "qc": "qc",
        "quality control": "qc",
        "input validation": "qc",
        "\u8d28\u63a7": "qc",
        "pca": "pca",
        "\u4e3b\u6210\u5206": "pca",
        "structure": "population_structure",
        "\u7fa4\u4f53\u7ed3\u6784": "population_structure",
        "fst": "population_statistics",
        "tajima": "population_statistics",
        "roh": "roh",
        "ld": "ld",
        "grm": "grm",
        "relationship matrix": "relationship_matrix",
        "relatedness": "relationship_matrix",
        "kinship": "kinship",
        "\u4eb2\u7f18\u5173\u7cfb": "kinship",
        "gwas": "gwas",
        "heritability": "heritability",
        "\u9057\u4f20\u529b": "heritability",
        "gblup": "genomic_prediction",
        "ssgblup": "genomic_prediction",
        "genomic prediction": "genomic_prediction",
        "bayes": "bayesian_prediction",
        "genomic selection": "genomic_prediction",
        "\u57fa\u56e0\u7ec4\u9009\u62e9": "genomic_prediction",
        "\u80b2\u79cd\u503c": "breeding_value_prediction",
        "breeding value": "breeding_value_prediction",
    }
    _risk_patterns = {
        "overwrite": "overwrite_results",
        "\u8986\u76d6": "overwrite_results",
        "delete": "delete_files",
        "\u5220\u9664": "delete_files",
        "rerun": "requeue_failed_job",
        "\u91cd\u8dd1": "requeue_failed_job",
        "rebuild": "bulk_recompute",
        "\u91cd\u5efa": "bulk_recompute",
        "all samples": "bulk_recompute",
        "\u5168\u91cf": "bulk_recompute",
        "upload": "external_upload_request",
        "\u4e0a\u4f20": "external_upload_request",
    }

    def analyze(self, request_text: str) -> IntentClassification:
        """Classify a request and capture deterministic planning hints."""

        normalized = request_text.lower()
        bio_hits = sorted(keyword for keyword in self._bioinformatics_keywords if keyword in normalized)
        system_hits = sorted(keyword for keyword in self._system_keywords if keyword in normalized)
        matched_keywords = sorted(set(bio_hits + system_hits))
        analysis_targets = sorted(
            {
                target
                for keyword, target in self._analysis_targets.items()
                if keyword in normalized
            }
        )
        risk_hints = sorted(
            {
                hint
                for keyword, hint in self._risk_patterns.items()
                if keyword in normalized
            }
        )

        if bio_hits and not system_hits:
            domain = TaskDomain.BIOINFORMATICS
        elif system_hits and not bio_hits:
            domain = TaskDomain.SYSTEM
        elif bio_hits and system_hits:
            domain = (
                TaskDomain.SYSTEM
                if any(
                    token in normalized
                    for token in {"error", "log", "\u62a5\u9519", "\u65e5\u5fd7"}
                )
                else TaskDomain.BIOINFORMATICS
            )
        else:
            domain = TaskDomain.KNOWLEDGE

        return IntentClassification(
            domain=domain,
            matched_keywords=matched_keywords,
            analysis_targets=analysis_targets,
            risk_hints=risk_hints,
            requires_retrieval=True,
        )

    def classify(self, request_text: str) -> TaskDomain:
        """Backwards-compatible domain-only classification helper."""

        return self.analyze(request_text).domain
