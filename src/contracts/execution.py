"""Execution-chain contracts shared by orchestration, safety, scheduler, and runtime."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import GateDecision, JobState, RiskLevel, RoleOutputHeader, SchedulerKind, TaskDomain
from contracts.tasks import ResourceEstimate, UserRequest


class RunContext(BaseModel):
    """Stable identity carried across one task and one concrete run."""

    task_id: str
    run_id: str
    session_id: str | None = None
    working_directory: str | None = None


class PipelineSpec(BaseModel):
    """Pipeline-level execution blueprint referenced by draft plans and dry-runs."""

    name: str
    domain: TaskDomain
    stages: list[str] = Field(default_factory=list)
    input_paths: list[str] = Field(default_factory=list)
    requested_outputs: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)


class TaskPlan(BaseModel):
    """Draft orchestration output for the current execution chain."""

    header: RoleOutputHeader
    run_context: RunContext
    summary: str
    domain: TaskDomain
    workflow_name: str
    workflow_steps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    pipeline_spec: PipelineSpec | None = None
    resource_estimate: ResourceEstimate | None = None


class ExecutionRequest(BaseModel):
    """Normalized internal request used to drive planning and execution."""

    run_context: RunContext
    user_request: UserRequest
    pipeline_spec: PipelineSpec | None = None
    resource_estimate: ResourceEstimate | None = None


class SubmissionSpec(BaseModel):
    """Scheduler-facing specification for dry-run or real submission."""

    run_context: RunContext
    scheduler: SchedulerKind
    working_directory: str
    command: list[str] = Field(default_factory=list)
    resource_estimate: ResourceEstimate
    conda_env_name: str | None = None


class SafetyReviewRequest(BaseModel):
    """Structured request passed through the safety gate."""

    run_context: RunContext
    action_name: str
    reason: str | None = None
    target_paths: list[str] = Field(default_factory=list)
    requested_resources: ResourceEstimate | None = None


class SafetyReviewResult(BaseModel):
    """Structured safety review output shared with API, CLI, and tests."""

    run_context: RunContext
    risk_level: RiskLevel
    decision: GateDecision
    requires_human_confirmation: bool
    reasons: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)


class ExecutionArtifacts(BaseModel):
    """Traceable artifacts produced by dry-run or execution planning."""

    run_context: RunContext
    script_preview: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    result_paths: list[str] = Field(default_factory=list)
    report_paths: list[str] = Field(default_factory=list)


class JobHandle(BaseModel):
    """Scheduler-facing handle returned after dry-run or submit actions."""

    run_context: RunContext
    scheduler: SchedulerKind
    job_id: str
    state: JobState = JobState.DRAFT
    stdout_path: str | None = None
    stderr_path: str | None = None


class SubmissionPreview(BaseModel):
    """Combined dry-run payload returned to entry points."""

    run_context: RunContext
    working_directory: str
    command: list[str] = Field(default_factory=list)
    script_preview: str
    job_handle: JobHandle
    artifacts: ExecutionArtifacts | None = None
