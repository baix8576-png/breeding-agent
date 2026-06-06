"""Contracts for PC-control-plane to remote Linux execution-plane operation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from contracts.common import ExecutionMode, JobState, SchedulerKind, SshAuthMode


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RemoteExecutionProfile(BaseModel):
    """SSH target description without credentials or secret material."""

    profile_name: str = "default"
    host: str | None = None
    user: str | None = None
    port: int = 22
    work_root: str = "/cluster/work/geneagent"
    allowed_write_roots: list[str] = Field(default_factory=list)
    default_partition: str | None = None
    tool_paths: dict[str, str] = Field(default_factory=dict)
    ssh_binary: str = "ssh"
    ssh_auth_mode: SshAuthMode = SshAuthMode.BATCH
    ssh_control_path: str | None = None
    ssh_control_persist: str = "4h"
    ssh_password: SecretStr | None = Field(default=None, exclude=True, repr=False)
    strict_host_key_checking: str = "accept-new"
    connect_timeout_seconds: int = 15

    model_config = ConfigDict(extra="forbid")

    @property
    def ssh_target(self) -> str | None:
        if not self.host:
            return None
        if self.user:
            return f"{self.user}@{self.host}"
        return self.host

    @property
    def ssh_password_configured(self) -> bool:
        return self.ssh_password is not None and bool(self.ssh_password.get_secret_value())


class ManualSubmitCard(BaseModel):
    """Copyable SBASE/web-console fields for manual fallback submission."""

    scheduler: str = "slurm"
    profile_name: str = "default"
    working_directory: str
    command_text: str
    partition: str | None = None
    cpus: int
    memory_gb: int
    walltime: str
    stdout_path: str
    stderr_path: str
    sbatch_wrap_command: str
    sbase_steps: list[str] = Field(default_factory=list)


class RemoteCheckResult(BaseModel):
    """Preflight summary for SSH, backend commands, tools, and work root."""

    profile_name: str = "default"
    execution_mode: ExecutionMode = ExecutionMode.SSH_SLURM_TRUSTED
    scheduler: SchedulerKind = SchedulerKind.SLURM
    ssh_target: str | None = None
    work_root: str | None = None
    reachable: bool = False
    safe_for_submit: bool = False
    command_checks: dict[str, bool] = Field(default_factory=dict)
    tool_checks: dict[str, bool] = Field(default_factory=dict)
    missing_commands: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    checked_at: str = Field(default_factory=_utc_now)


class RemoteSmokeResult(BaseModel):
    """Harmless remote execution smoke result for operator-gated server validation."""

    profile_name: str = "default"
    execution_mode: ExecutionMode = ExecutionMode.SSH_SHELL_TRUSTED
    command: list[str] = Field(default_factory=list)
    remote_check: RemoteCheckResult
    submitted: bool = False
    job_handle: Any = None
    initial_state: JobState | None = None
    run_state_path: str | None = None
    messages: list[str] = Field(default_factory=list)
    checked_at: str = Field(default_factory=_utc_now)


class RunStageRecord(BaseModel):
    """One persisted stage transition for trusted remote automation."""

    stage_id: str
    status: str
    message: str | None = None
    job_id: str | None = None
    updated_at: str = Field(default_factory=_utc_now)


class RunState(BaseModel):
    """Local durable state for submit, watch, repair, and resume loops."""

    schema_version: str = "run_state.v1"
    task_id: str
    run_id: str
    execution_mode: ExecutionMode = ExecutionMode.SSH_SLURM_TRUSTED
    remote_profile_name: str | None = None
    scheduler: SchedulerKind = SchedulerKind.SLURM
    working_directory: str
    current_stage: str = "stage_07_execution"
    status: JobState = JobState.DRAFT
    job_id: str | None = None
    auto_continue: bool = False
    auto_continue_ready: bool = False
    auto_repair_attempts: int = 0
    repeated_failures: int = 0
    next_action: str = "watch scheduler state"
    state_path: str | None = None
    stages: list[RunStageRecord] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utc_now)
    updated_at: str = Field(default_factory=_utc_now)

    def with_stage(
        self,
        *,
        stage_id: str,
        status: str,
        message: str | None = None,
        job_id: str | None = None,
        next_action: str | None = None,
        current_stage: str | None = None,
        run_status: JobState | None = None,
        auto_continue_ready: bool | None = None,
    ) -> "RunState":
        """Return a copy with one stage transition appended."""

        return self.model_copy(
            update={
                "current_stage": current_stage or stage_id,
                "status": run_status or self.status,
                "job_id": job_id or self.job_id,
                "next_action": next_action or self.next_action,
                "auto_continue_ready": (
                    self.auto_continue_ready if auto_continue_ready is None else auto_continue_ready
                ),
                "stages": [
                    *self.stages,
                    RunStageRecord(
                        stage_id=stage_id,
                        status=status,
                        message=message,
                        job_id=job_id or self.job_id,
                    ),
                ],
                "updated_at": _utc_now(),
            }
        )
