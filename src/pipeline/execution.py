"""Execution command planning for concrete v1 bioinformatics workflows."""

from __future__ import annotations

import os
import re
from pathlib import Path

from pydantic import BaseModel, Field

from contracts.execution import PipelineSpec


class PipelineExecutionPlan(BaseModel):
    """Resolved execution plan for one concrete pipeline submission."""

    pipeline_name: str
    script_path: str
    command: list[str] = Field(default_factory=list)
    analysis_targets: list[str] = Field(default_factory=list)
    algorithms: list[str] = Field(default_factory=list)


_PIPELINE_SCRIPT = {
    "qc_pipeline": "qc_pipeline/run_qc_pipeline.sh",
    "pca_pipeline": "pca_pipeline/run_pca_pipeline.sh",
    "grm_builder": "grm_builder/run_grm_builder.sh",
    "genomic_prediction": "genomic_prediction/run_genomic_prediction.sh",
}

_PIPELINE_ALIASES = {
    "population_structure": "pca_pipeline",
    "grm_construction": "grm_builder",
    "genomic_selection": "genomic_prediction",
}

_TARGET_ALIASES = {
    "population_structure": ["pca", "population_structure"],
    "population_statistics": ["fst", "pi", "tajima_d"],
    "relationship_matrix": ["grm", "kinship"],
    "breeding_value_prediction": ["genomic_prediction"],
    "bayesian_prediction": ["genomic_prediction"],
}

_DEFAULT_TARGETS = {
    "qc_pipeline": ["qc", "sample_qc", "variant_qc"],
    "pca_pipeline": ["pca", "population_structure", "ld", "roh", "fst", "pi", "tajima_d"],
    "grm_builder": ["grm", "kinship"],
    "genomic_prediction": ["gwas", "heritability", "genomic_prediction"],
}

_PIPELINE_UMBRELLA_TARGET = {
    "qc_pipeline": "qc",
    "pca_pipeline": "pca",
    "grm_builder": "grm",
    "genomic_prediction": "genomic_prediction",
}

_TARGET_ALGORITHMS = {
    "qc": ["plink2_missingness", "plink2_hwe", "plink2_allele_frequency", "bcftools_stats"],
    "sample_qc": ["plink2_missingness"],
    "variant_qc": ["plink2_hwe", "plink2_allele_frequency"],
    "pca": ["plink2_indep_pairwise", "plink2_pca"],
    "population_structure": ["plink2_indep_pairwise", "plink2_pca"],
    "ld": ["plink2_r2"],
    "roh": ["plink2_homozyg"],
    "fst": ["vcftools_weir_fst"],
    "pi": ["vcftools_window_pi"],
    "tajima_d": ["vcftools_tajima_d"],
    "grm": ["plink2_make_rel", "gcta_make_grm"],
    "kinship": ["plink2_make_rel"],
    "gwas": ["plink2_glm"],
    "heritability": ["gcta_reml"],
    "genomic_prediction": ["gcta_reml_pred_rand", "gcta_grm_blup"],
}


def build_execution_plan(
    pipeline_spec: PipelineSpec,
    *,
    request_text: str,
    working_directory: str,
    script_root: str | None = None,
) -> PipelineExecutionPlan:
    """Build a concrete script command for the selected bioinformatics pipeline."""

    pipeline_name = _canonical_pipeline_name(pipeline_spec.name)
    script_path = _resolve_script_path(pipeline_name=pipeline_name, script_root=script_root)
    analysis_targets = _resolve_analysis_targets(pipeline_spec=pipeline_spec, request_text=request_text)
    algorithms = _resolve_algorithms(analysis_targets)
    command = [
        "bash",
        str(script_path),
        "--workdir",
        working_directory,
        "--analysis-targets",
        ",".join(analysis_targets),
        "--request-text",
        request_text,
    ]
    return PipelineExecutionPlan(
        pipeline_name=pipeline_name,
        script_path=str(script_path),
        command=command,
        analysis_targets=analysis_targets,
        algorithms=algorithms,
    )


def build_execution_command(
    pipeline_spec: PipelineSpec,
    *,
    request_text: str,
    working_directory: str,
    script_root: str | None = None,
) -> list[str]:
    """Shortcut helper returning only the command vector."""

    return build_execution_plan(
        pipeline_spec,
        request_text=request_text,
        working_directory=working_directory,
        script_root=script_root,
    ).command


def _canonical_pipeline_name(name: str) -> str:
    return _PIPELINE_ALIASES.get(name, name)


def _resolve_script_path(*, pipeline_name: str, script_root: str | None) -> Path:
    relative = _PIPELINE_SCRIPT.get(pipeline_name)
    if relative is None:
        available = ", ".join(sorted(_PIPELINE_SCRIPT))
        raise ValueError(f"Unsupported pipeline '{pipeline_name}'. Available: {available}.")
    root = Path(script_root) if script_root else _default_script_root()
    script_path = root / relative
    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline script does not exist: {script_path}")
    return script_path


def _default_script_root() -> Path:
    env_path = os.getenv("GENEAGENT_SCRIPT_ROOT")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parents[2] / "scripts"


def _resolve_analysis_targets(pipeline_spec: PipelineSpec, request_text: str) -> list[str]:
    pipeline_name = _canonical_pipeline_name(pipeline_spec.name)
    defaults = _DEFAULT_TARGETS.get(pipeline_name, [])

    explicit_targets = [_normalize_target(item) for item in pipeline_spec.analysis_targets]
    text_targets = _extract_targets_from_text(request_text)
    merged_raw = [item for item in [*explicit_targets, *text_targets] if item]
    expanded: list[str] = []
    for raw_target in merged_raw:
        if raw_target in _TARGET_ALIASES:
            expanded.extend(_TARGET_ALIASES[raw_target])
        else:
            expanded.append(raw_target)

    candidate_targets = _stable_unique(expanded)
    allowed_targets = set(_DEFAULT_TARGETS.get(pipeline_name, []))
    filtered = [target for target in candidate_targets if target in allowed_targets]

    if not filtered:
        return defaults
    umbrella_target = _PIPELINE_UMBRELLA_TARGET.get(pipeline_name)
    if umbrella_target is not None and len(filtered) == 1 and filtered[0] == umbrella_target:
        return defaults

    ordered = [target for target in defaults if target in filtered]
    extras = [target for target in filtered if target not in ordered]
    return ordered + extras


def _normalize_target(value: str) -> str:
    lowered = value.strip().lower()
    lowered = lowered.replace("-", "_").replace(" ", "_")
    lowered = re.sub(r"[^a-z0-9_]+", "", lowered)
    return lowered


def _extract_targets_from_text(text: str) -> list[str]:
    lowered = text.lower()
    matched: list[str] = []
    keywords = {
        "qc": "qc",
        "quality control": "qc",
        "input validation": "qc",
        "pca": "pca",
        "structure": "population_structure",
        "ld": "ld",
        "roh": "roh",
        "fst": "fst",
        "tajima": "tajima_d",
        "pi": "pi",
        "grm": "grm",
        "kinship": "kinship",
        "relatedness": "kinship",
        "gwas": "gwas",
        "heritability": "heritability",
        "genomic prediction": "genomic_prediction",
        "genomic selection": "genomic_prediction",
        "breeding value": "genomic_prediction",
        "gblup": "genomic_prediction",
        "ssgblup": "genomic_prediction",
    }
    for keyword, target in keywords.items():
        if keyword in lowered:
            matched.append(target)
    return _stable_unique(_normalize_target(item) for item in matched)


def _resolve_algorithms(analysis_targets: list[str]) -> list[str]:
    algorithms: list[str] = []
    for target in analysis_targets:
        for algorithm in _TARGET_ALGORITHMS.get(target, []):
            if algorithm not in algorithms:
                algorithms.append(algorithm)
    return algorithms


def _stable_unique(items) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
