"""Scheduler-internal models for resource planning and polling explanations."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import JobState, SchedulerKind
from contracts.execution import JobHandle


class SchedulerPaths(BaseModel):
    """Resolved filesystem paths used by scheduler planning."""

    working_directory: str
    script_path: str
    stdout_path: str
    stderr_path: str


class SchedulerResourceRequest(BaseModel):
    """Normalized scheduler request derived from a coarse resource estimate."""

    job_name: str = "geneagent-job"
    nodes: int = 1
    tasks: int = 1
    cpus_per_task: int = 4
    memory_gb: int = 16
    walltime: str = "04:00:00"
    partition: str | None = None
    account: str | None = None
    qos: str | None = None
    conda_env_name: str | None = None
    environment_exports: dict[str, str] = Field(default_factory=dict)
    conservative_default: bool = True
    scheduler_hints: list[str] = Field(default_factory=list)

    @property
    def total_cpus(self) -> int:
        """Return the total CPU request implied by tasks and CPUs per task."""

        return max(1, self.tasks * self.cpus_per_task)


class SubmissionPlan(BaseModel):
    """Dry-run or submit-preview plan built without touching a real cluster."""

    task_id: str
    run_id: str
    scheduler: SchedulerKind
    mode: str = "dry-run"
    ready_for_gate: str = "scheduler_plan_ready"
    resource_request: SchedulerResourceRequest
    paths: SchedulerPaths
    command: list[str] = Field(default_factory=list)
    command_preview: str
    script_preview: str
    submit_command: list[str] = Field(default_factory=list)
    job_handle: JobHandle
    warnings: list[str] = Field(default_factory=list)
    compatibility_notes: list[str] = Field(default_factory=list)
    polling_hint: str | None = None


class PollExplanation(BaseModel):
    """Human-readable interpretation of a scheduler state."""

    scheduler: SchedulerKind
    job_id: str
    state: JobState
    recommended_action: str
    explanation: str
    poll_command_hint: str | None = None
    terminal: bool = False
