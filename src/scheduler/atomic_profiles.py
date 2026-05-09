"""Atomic algorithm resource and failure guidance for scheduler planning."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from contracts.tasks import ResourceEstimate


class AtomicFailureCodeMapping(BaseModel):
    """Failure code behavior for one atomic algorithm."""

    model_config = ConfigDict(extra="forbid")

    code: str
    retryable: bool = False
    retry_suggestion: str


class AtomicToolProfile(BaseModel):
    """Resource and retry profile for one atomic algorithm."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str
    cpus: int = Field(ge=1)
    memory_gb: int = Field(ge=1)
    walltime: str
    retry_suggestion: str
    failure_code_map: list[AtomicFailureCodeMapping] = Field(default_factory=list)


def _profile(
    *,
    tool_name: str,
    cpus: int,
    memory_gb: int,
    walltime: str,
    retry_suggestion: str,
    failure_codes: list[tuple[str, bool, str]],
) -> AtomicToolProfile:
    return AtomicToolProfile(
        tool_name=tool_name,
        cpus=cpus,
        memory_gb=memory_gb,
        walltime=walltime,
        retry_suggestion=retry_suggestion,
        failure_code_map=[
            AtomicFailureCodeMapping(
                code=code,
                retryable=retryable,
                retry_suggestion=suggestion,
            )
            for code, retryable, suggestion in failure_codes
        ],
    )


_ATOMIC_TOOL_PROFILES: dict[str, AtomicToolProfile] = {
    "plink2_missingness": _profile(
        tool_name="plink2_missingness",
        cpus=4,
        memory_gb=12,
        walltime="01:00:00",
        retry_suggestion="Increase memory by +25% and retry once after checking missingness thresholds.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_hwe": _profile(
        tool_name="plink2_hwe",
        cpus=4,
        memory_gb=12,
        walltime="01:00:00",
        retry_suggestion="Increase memory by +25% and retry once after validating HWE threshold.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_allele_frequency": _profile(
        tool_name="plink2_allele_frequency",
        cpus=4,
        memory_gb=12,
        walltime="01:00:00",
        retry_suggestion="Recheck PLINK prefix, then retry once with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "bcftools_stats": _profile(
        tool_name="bcftools_stats",
        cpus=2,
        memory_gb=8,
        walltime="00:45:00",
        retry_suggestion="Rebuild VCF index and retry once.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix VCF path contract."),
            ("IO_ERROR", True, "Validate storage mount and VCF index."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_indep_pairwise": _profile(
        tool_name="plink2_indep_pairwise",
        cpus=8,
        memory_gb=24,
        walltime="03:00:00",
        retry_suggestion="Reduce LD window and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_pca": _profile(
        tool_name="plink2_pca",
        cpus=12,
        memory_gb=48,
        walltime="06:00:00",
        retry_suggestion="Reduce PCs or increase memory by +25%, then retry once.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_r2": _profile(
        tool_name="plink2_r2",
        cpus=12,
        memory_gb=48,
        walltime="06:00:00",
        retry_suggestion="Shard by chromosome and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_homozyg": _profile(
        tool_name="plink2_homozyg",
        cpus=8,
        memory_gb=24,
        walltime="04:00:00",
        retry_suggestion="Relax ROH parameters and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "vcftools_weir_fst": _profile(
        tool_name="vcftools_weir_fst",
        cpus=6,
        memory_gb=16,
        walltime="02:30:00",
        retry_suggestion="Split by chromosome/population pair and increase walltime by +50%.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix VCF/population panel contract."),
            ("WALLTIME_EXCEEDED", True, "Increase walltime by +50%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "vcftools_window_pi": _profile(
        tool_name="vcftools_window_pi",
        cpus=6,
        memory_gb=16,
        walltime="02:30:00",
        retry_suggestion="Shard by chromosome and increase walltime by +50%.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix VCF contract."),
            ("WALLTIME_EXCEEDED", True, "Increase walltime by +50%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "vcftools_tajima_d": _profile(
        tool_name="vcftools_tajima_d",
        cpus=6,
        memory_gb=16,
        walltime="02:30:00",
        retry_suggestion="Shard by chromosome and increase walltime by +50%.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix VCF contract."),
            ("WALLTIME_EXCEEDED", True, "Increase walltime by +50%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_make_rel": _profile(
        tool_name="plink2_make_rel",
        cpus=8,
        memory_gb=24,
        walltime="03:30:00",
        retry_suggestion="Shard by chromosome and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix bed/bim/fam contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "gcta_make_grm": _profile(
        tool_name="gcta_make_grm",
        cpus=16,
        memory_gb=64,
        walltime="08:00:00",
        retry_suggestion="Split chromosome batches and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix PLINK/GRM path contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "plink2_glm": _profile(
        tool_name="plink2_glm",
        cpus=16,
        memory_gb=64,
        walltime="10:00:00",
        retry_suggestion="Reduce covariates or split traits, then retry.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix genotype/phenotype path contract."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "gcta_reml": _profile(
        tool_name="gcta_reml",
        cpus=16,
        memory_gb=96,
        walltime="12:00:00",
        retry_suggestion="Drop collinear covariates and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix GRM/phenotype path contract."),
            ("MATRIX_SINGULAR", True, "Adjust covariates and retry."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "gcta_reml_pred_rand": _profile(
        tool_name="gcta_reml_pred_rand",
        cpus=16,
        memory_gb=96,
        walltime="12:00:00",
        retry_suggestion="Drop collinear covariates and retry with +25% memory.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix GRM/phenotype path contract."),
            ("MATRIX_SINGULAR", True, "Adjust covariates and retry."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
    "gcta_grm_blup": _profile(
        tool_name="gcta_grm_blup",
        cpus=12,
        memory_gb=48,
        walltime="06:00:00",
        retry_suggestion="Split traits and retry with adjusted model terms.",
        failure_codes=[
            ("INPUT_MISSING", False, "Fix GRM/phenotype path contract."),
            ("MATRIX_SINGULAR", True, "Adjust covariates and retry."),
            ("OUT_OF_MEMORY", True, "Increase memory by +25%."),
            ("NONZERO_EXIT", True, "Inspect stderr and retry once."),
        ],
    ),
}


def list_atomic_tool_profiles() -> list[AtomicToolProfile]:
    """Return all atomic tool profiles in stable order."""

    return [profile.model_copy(deep=True) for _, profile in sorted(_ATOMIC_TOOL_PROFILES.items())]


def get_atomic_tool_profile(tool_name: str) -> AtomicToolProfile | None:
    """Return one atomic tool profile, or None when unknown."""

    profile = _ATOMIC_TOOL_PROFILES.get(tool_name)
    if profile is None:
        return None
    return profile.model_copy(deep=True)


def estimate_resources_for_atomic_tools(
    tool_names: list[str],
    *,
    requested_partition: str | None = None,
) -> ResourceEstimate:
    """Aggregate one conservative resource estimate for atomic tool bundles."""

    known = [profile for name in _stable_unique(tool_names) if (profile := _ATOMIC_TOOL_PROFILES.get(name))]
    if not known:
        return ResourceEstimate(
            cpus=4,
            memory_gb=16,
            walltime="04:00:00",
            partition=requested_partition,
            conservative_default=True,
        )

    max_cpus = max(profile.cpus for profile in known)
    max_memory = max(profile.memory_gb for profile in known)
    walltime_seconds = int(sum(_walltime_to_seconds(profile.walltime) for profile in known) * 1.15)
    return ResourceEstimate(
        cpus=max(1, max_cpus),
        memory_gb=max(1, max_memory),
        walltime=_seconds_to_walltime(max(600, walltime_seconds)),
        partition=requested_partition,
        conservative_default=False,
    )


def failure_code_mapping_for_atomic_tools(tool_names: list[str]) -> dict[str, list[dict[str, object]]]:
    """Return structured failure code mapping for the requested atomic tools."""

    mapping: dict[str, list[dict[str, object]]] = {}
    for tool_name in _stable_unique(tool_names):
        profile = _ATOMIC_TOOL_PROFILES.get(tool_name)
        if profile is None:
            continue
        mapping[tool_name] = [
            {
                "code": item.code,
                "retryable": item.retryable,
                "retry_suggestion": item.retry_suggestion,
            }
            for item in profile.failure_code_map
        ]
    return mapping


def summarize_retry_guidance(tool_names: list[str]) -> list[str]:
    """Build scheduler-facing retry guidance lines for failure recovery."""

    lines: list[str] = []
    for tool_name in _stable_unique(tool_names):
        profile = _ATOMIC_TOOL_PROFILES.get(tool_name)
        if profile is None:
            continue
        lines.append(
            f"{tool_name}: cpus={profile.cpus}, memory_gb={profile.memory_gb}, walltime={profile.walltime}; "
            f"retry={profile.retry_suggestion}"
        )
    return lines


def _walltime_to_seconds(walltime: str) -> int:
    parts = walltime.split(":")
    if len(parts) != 3:
        return 4 * 3600
    try:
        hours, minutes, seconds = (int(part) for part in parts)
    except ValueError:
        return 4 * 3600
    return max(0, hours * 3600 + minutes * 60 + seconds)


def _seconds_to_walltime(value: int) -> str:
    seconds = max(0, int(value))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remain = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remain:02d}"


def _stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
