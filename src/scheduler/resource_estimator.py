"""Conservative resource estimation with SLURM-first workload profiles."""

from __future__ import annotations

from contracts.common import TaskDomain
from contracts.tasks import ResourceEstimate
from scheduler.atomic_profiles import (
    estimate_resources_for_atomic_tools,
    failure_code_mapping_for_atomic_tools,
)


class ConservativeResourceEstimator:
    """Map task domains and common workloads to conservative resource profiles."""

    _DOMAIN_PROFILES: dict[TaskDomain, ResourceEstimate] = {
        TaskDomain.BIOINFORMATICS: ResourceEstimate(
            cpus=8,
            memory_gb=32,
            walltime="08:00:00",
            conservative_default=True,
        ),
        TaskDomain.SYSTEM: ResourceEstimate(
            cpus=2,
            memory_gb=4,
            walltime="00:30:00",
            conservative_default=True,
        ),
        TaskDomain.KNOWLEDGE: ResourceEstimate(
            cpus=2,
            memory_gb=8,
            walltime="01:00:00",
            conservative_default=True,
        ),
    }

    _WORKLOAD_PROFILES: dict[str, ResourceEstimate] = {
        "qc_pipeline": ResourceEstimate(cpus=4, memory_gb=16, walltime="02:00:00", conservative_default=False),
        "pca_pipeline": ResourceEstimate(cpus=8, memory_gb=32, walltime="06:00:00", conservative_default=False),
        "grm_builder": ResourceEstimate(cpus=16, memory_gb=64, walltime="10:00:00", conservative_default=False),
        "gwas": ResourceEstimate(cpus=16, memory_gb=64, walltime="12:00:00", conservative_default=False),
        "genomic_prediction": ResourceEstimate(
            cpus=16,
            memory_gb=96,
            walltime="16:00:00",
            conservative_default=False,
        ),
        "report_generator": ResourceEstimate(
            cpus=2,
            memory_gb=8,
            walltime="00:30:00",
            conservative_default=False,
        ),
    }

    def __init__(self, default_partition: str | None) -> None:
        self._default_partition = default_partition

    def estimate_for_domain(self, domain: TaskDomain) -> ResourceEstimate:
        """Return a conservative resource estimate for the selected domain."""

        profile = self._DOMAIN_PROFILES.get(domain, self._DOMAIN_PROFILES[TaskDomain.KNOWLEDGE])
        return profile.model_copy(update={"partition": self._default_partition})

    def estimate_for_workload(
        self,
        workload_name: str,
        *,
        requested_partition: str | None = None,
        requested_cpus: int | None = None,
        requested_memory_gb: int | None = None,
        requested_walltime: str | None = None,
    ) -> ResourceEstimate:
        """Return a workload-aware estimate while keeping conservative lower bounds."""

        profile = self._WORKLOAD_PROFILES.get(
            workload_name,
            ResourceEstimate(cpus=4, memory_gb=16, walltime="04:00:00", conservative_default=True),
        )
        return profile.model_copy(
            update={
                "cpus": max(1, requested_cpus or profile.cpus),
                "memory_gb": max(1, requested_memory_gb or profile.memory_gb),
                "walltime": requested_walltime or profile.walltime,
                "partition": requested_partition or self._default_partition,
            }
        )

    def estimate_for_atomic_tools(
        self,
        atomic_tools: list[str],
        *,
        requested_partition: str | None = None,
    ) -> ResourceEstimate:
        """Aggregate resources from atomic algorithm profiles."""

        return estimate_resources_for_atomic_tools(
            atomic_tools,
            requested_partition=requested_partition or self._default_partition,
        )

    def failure_code_mapping_for_atomic_tools(self, atomic_tools: list[str]) -> dict[str, list[dict[str, object]]]:
        """Expose atomic failure-code mapping for planning and diagnostics."""

        return failure_code_mapping_for_atomic_tools(atomic_tools)

    def merge_estimates(self, *estimates: ResourceEstimate) -> ResourceEstimate:
        """Merge one or more estimates using conservative upper bounds."""

        valid = [estimate for estimate in estimates if estimate is not None]
        if not valid:
            return ResourceEstimate(partition=self._default_partition)
        return ResourceEstimate(
            cpus=max(item.cpus for item in valid),
            memory_gb=max(item.memory_gb for item in valid),
            walltime=max((item.walltime for item in valid), key=self._walltime_to_seconds),
            partition=next(
                (item.partition for item in valid if item.partition),
                self._default_partition,
            ),
            conservative_default=all(item.conservative_default for item in valid),
        )

    def _walltime_to_seconds(self, walltime: str) -> int:
        parts = walltime.split(":")
        if len(parts) != 3:
            return 0
        try:
            hours, minutes, seconds = (int(part) for part in parts)
        except ValueError:
            return 0
        return max(0, hours * 3600 + minutes * 60 + seconds)
