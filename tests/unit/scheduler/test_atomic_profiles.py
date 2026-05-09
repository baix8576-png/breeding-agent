from __future__ import annotations

from contracts.tasks import ResourceEstimate
from scheduler.atomic_profiles import (
    estimate_resources_for_atomic_tools,
    failure_code_mapping_for_atomic_tools,
    get_atomic_tool_profile,
)
from scheduler.slurm import SlurmSchedulerAdapter


def test_atomic_profiles_expose_known_tools() -> None:
    profile = get_atomic_tool_profile("plink2_pca")

    assert profile is not None
    assert profile.cpus >= 8
    assert profile.memory_gb >= 24
    assert profile.failure_code_map


def test_atomic_resource_estimate_aggregates_tool_bundle() -> None:
    estimate = estimate_resources_for_atomic_tools(
        ["plink2_pca", "vcftools_weir_fst", "gcta_reml"],
        requested_partition="long",
    )

    assert estimate.partition == "long"
    assert estimate.cpus >= 16
    assert estimate.memory_gb >= 96
    assert estimate.walltime >= "12:00:00"
    assert estimate.conservative_default is False


def test_submission_plan_embeds_atomic_failure_mapping_and_retry_guidance() -> None:
    adapter = SlurmSchedulerAdapter()
    plan = adapter.build_submission_plan(
        command=["bash", "scripts/pca_pipeline/run_pca_pipeline.sh"],
        working_directory="/cluster/work/demo",
        resources=ResourceEstimate(cpus=4, memory_gb=16, walltime="01:00:00"),
        task_id="task-atomic-001",
        run_id="run-atomic-001",
        atomic_tools=["plink2_pca", "vcftools_weir_fst"],
    )

    assert "plink2_pca" in plan.atomic_tools
    assert "vcftools_weir_fst" in plan.atomic_tools
    assert "plink2_pca" in plan.atomic_failure_code_mapping
    assert any("atomic tool retry guidance" in line for line in plan.failure_recovery)
    assert plan.resource_request.cpus_per_task >= 12
    assert plan.resource_request.memory_gb >= 48


def test_atomic_failure_mapping_contains_retry_metadata() -> None:
    mapping = failure_code_mapping_for_atomic_tools(["gcta_reml"])

    assert "gcta_reml" in mapping
    assert any(item["code"] == "MATRIX_SINGULAR" for item in mapping["gcta_reml"])
    assert any(item["retryable"] for item in mapping["gcta_reml"])
