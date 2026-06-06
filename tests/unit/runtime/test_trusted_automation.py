from __future__ import annotations

import json
import subprocess

from contracts.common import ExecutionMode, JobState, SchedulerKind
from contracts.execution import JobHandle, RunContext
from contracts.remote_execution import RemoteCheckResult
from contracts.tasks import ResourceEstimate
from runtime.bootstrap import create_application_context
from runtime.settings import Settings


class SmokeScheduler:
    def __init__(self) -> None:
        self.submissions: list[dict[str, object]] = []

    def submit(
        self,
        working_directory: str,
        resources: ResourceEstimate,
        command: list[str] | None = None,
        job_name: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
        atomic_tools: list[str] | None = None,
    ) -> JobHandle:
        self.submissions.append(
            {
                "working_directory": working_directory,
                "resources": resources,
                "command": command,
                "job_name": job_name,
                "task_id": task_id,
                "run_id": run_id,
                "atomic_tools": atomic_tools,
            }
        )
        return JobHandle(
            run_context=RunContext(
                task_id=task_id or "task-smoke",
                run_id=run_id or "run-smoke",
                working_directory=working_directory,
            ),
            scheduler=SchedulerKind.SHELL,
            job_id="shell:4242",
            state=JobState.RUNNING,
            stdout_path=f"{working_directory}/logs/stdout.log",
            stderr_path=f"{working_directory}/logs/stderr.log",
        )

    def poll(self, job_id: str) -> JobState:
        _ = job_id
        return JobState.RUNNING


def test_remote_smoke_blocks_when_remote_check_is_not_safe(monkeypatch, tmp_path) -> None:
    settings = Settings(
        execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
        scheduler_real_execution_enabled=True,
        hpc_host="server.example.org",
        hpc_user="alice",
        hpc_work_root="/data2/alice/geneagent_runs",
        local_state_root=str(tmp_path / ".geneagent"),
        _env_file=None,
    )
    context = create_application_context(settings=settings)
    fake_scheduler = SmokeScheduler()
    monkeypatch.setattr(
        context.facade,
        "remote_check",
        lambda **_kwargs: RemoteCheckResult(
            execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
            scheduler=SchedulerKind.SHELL,
            reachable=False,
            safe_for_submit=False,
            messages=["control_master_not_open"],
        ),
    )
    monkeypatch.setattr(context.facade, "_scheduler_for_execution_mode", lambda **_kwargs: fake_scheduler)

    result = context.facade.remote_smoke()

    assert result.submitted is False
    assert result.job_handle is None
    assert result.initial_state is None
    assert result.messages == ["control_master_not_open"]
    assert fake_scheduler.submissions == []


def test_remote_smoke_submits_fixed_safe_command_after_remote_check(monkeypatch, tmp_path) -> None:
    settings = Settings(
        execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
        scheduler_real_execution_enabled=True,
        hpc_host="server.example.org",
        hpc_user="alice",
        hpc_work_root="/data2/alice/geneagent_runs",
        local_state_root=str(tmp_path / ".geneagent"),
        _env_file=None,
    )
    context = create_application_context(settings=settings)
    fake_scheduler = SmokeScheduler()
    monkeypatch.setattr(
        context.facade,
        "remote_check",
        lambda **_kwargs: RemoteCheckResult(
            execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
            scheduler=SchedulerKind.SHELL,
            work_root="/data2/alice/geneagent_runs",
            reachable=True,
            safe_for_submit=True,
        ),
    )
    monkeypatch.setattr(context.facade, "_scheduler_for_execution_mode", lambda **_kwargs: fake_scheduler)

    result = context.facade.remote_smoke(task_id="task-smoke-001", run_id="run-smoke-001")

    assert result.submitted is True
    assert result.job_handle is not None
    assert result.job_handle.job_id == "shell:4242"
    assert result.initial_state == JobState.RUNNING
    assert result.command == ["bash", "-lc", "hostname && pwd && date && sleep 5"]
    assert fake_scheduler.submissions[0]["working_directory"] == "/data2/alice/geneagent_runs"
    assert fake_scheduler.submissions[0]["command"] == result.command
    assert fake_scheduler.submissions[0]["task_id"] == "task-smoke-001"
    assert fake_scheduler.submissions[0]["run_id"] == "run-smoke-001"
    assert result.run_state_path is not None
    state_payload = json.loads(Path(result.run_state_path).read_text(encoding="utf-8"))
    assert state_payload["task_id"] == "task-smoke-001"
    assert state_payload["run_id"] == "run-smoke-001"
    assert state_payload["execution_mode"] == "ssh_shell_trusted"
    assert state_payload["scheduler"] == "shell"
    assert state_payload["job_id"] == "shell:4242"
    assert state_payload["status"] == "running"
    assert state_payload["working_directory"] == "/data2/alice/geneagent_runs"
    assert state_payload["stages"][0]["status"] == "submitted"
    assert state_payload["stages"][0]["job_id"] == "shell:4242"

from pathlib import Path

from contracts.common import ExecutionMode, JobState, SchedulerKind
from contracts.remote_execution import RunState
from runtime.automation import TrustedRunController
from runtime.run_state import RunStateStore
from safety.automation_policy import AutomationPolicyDecision


class CompletingScheduler:
    def poll(self, job_id: str) -> JobState:
        assert job_id == "12345"
        return JobState.COMPLETED


class FailingScheduler:
    def poll(self, job_id: str) -> JobState:
        assert job_id == "12345"
        return JobState.FAILED


class RetryingScheduler:
    def __init__(self) -> None:
        self.retry_calls: list[RunState] = []

    def poll(self, job_id: str) -> JobState:
        assert job_id == "12345"
        return JobState.FAILED

    def retry_job(self, state: RunState) -> str:
        self.retry_calls.append(state)
        return "67890"


class RecordingAllowPolicy:
    def __init__(self) -> None:
        self.actions: list[str] = []

    def review(self, request):
        self.actions.append(request.action)
        return AutomationPolicyDecision(allowed=True, reason="test_policy_allowed")


class ShellRunScheduler:
    def __init__(self, state: JobState = JobState.RUNNING) -> None:
        self.state = state
        self.states: list[RunState] = []

    def poll_run(self, state: RunState) -> JobState:
        self.states.append(state)
        return self.state

    def poll(self, job_id: str) -> JobState:
        raise AssertionError(f"poll should not be used for shell run state: {job_id}")


def _queued_state() -> RunState:
    return RunState(
        task_id="task-auto-001",
        run_id="run-auto-001",
        execution_mode=ExecutionMode.SSH_SLURM_TRUSTED,
        remote_profile_name="prod",
        scheduler=SchedulerKind.SLURM,
        working_directory="/cluster/work/alice/geneagent/run-auto-001",
        current_stage="stage_07_execution",
        status=JobState.QUEUED,
        job_id="12345",
        auto_continue=True,
    )


def _shell_state() -> RunState:
    return RunState(
        task_id="task-shell-001",
        run_id="run-shell-001",
        execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
        remote_profile_name="server",
        scheduler=SchedulerKind.SHELL,
        working_directory="/data2/alice/geneagent_runs/task-shell-001/run-shell-001",
        current_stage="stage_07_execution",
        status=JobState.RUNNING,
        job_id="shell:4242",
        auto_continue=True,
    )


def test_trusted_run_controller_marks_completed_job_ready_for_next_stage(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")
    store.save(_queued_state())
    controller = TrustedRunController(state_store=store)

    updated = controller.watch_run(
        task_id="task-auto-001",
        run_id="run-auto-001",
        scheduler=CompletingScheduler(),
    )

    assert updated.status == JobState.COMPLETED
    assert updated.current_stage == "stage_08_artifact_and_report"
    assert updated.auto_continue_ready is True
    assert "completed" in updated.stages[-1].status


def test_trusted_run_controller_uses_run_state_poll_hook_for_shell_mode(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")
    store.save(_shell_state())
    scheduler = ShellRunScheduler()
    controller = TrustedRunController(state_store=store)

    updated = controller.watch_run(
        task_id="task-shell-001",
        run_id="run-shell-001",
        scheduler=scheduler,
    )

    assert len(scheduler.states) == 1
    assert scheduler.states[0].task_id == "task-shell-001"
    assert scheduler.states[0].run_id == "run-shell-001"
    assert updated.status == JobState.RUNNING
    assert updated.auto_continue_ready is False


def test_trusted_run_controller_breaks_shell_unknown_pid_without_auto_continue(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")
    store.save(_shell_state())
    scheduler = ShellRunScheduler(state=JobState.UNKNOWN)
    controller = TrustedRunController(state_store=store)

    updated = controller.watch_run(
        task_id="task-shell-001",
        run_id="run-shell-001",
        scheduler=scheduler,
    )

    assert updated.status == JobState.UNKNOWN
    assert updated.auto_continue_ready is False
    assert "manual review" in updated.next_action.lower()
    assert "shell pid" in (updated.stages[-1].message or "").lower()


def test_trusted_run_controller_classifies_failed_job_without_auto_overwrite(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")
    store.save(_queued_state())
    policy = RecordingAllowPolicy()
    controller = TrustedRunController(state_store=store, policy=policy)

    updated = controller.watch_run(
        task_id="task-auto-001",
        run_id="run-auto-001",
        scheduler=FailingScheduler(),
    )

    assert updated.status == JobState.FAILED
    assert updated.auto_continue_ready is False
    assert policy.actions == ["retry_transient_scheduler_failure"]
    assert "manual review" in updated.next_action.lower()


def test_trusted_run_controller_uses_policy_for_low_risk_retry(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")
    store.save(_queued_state())
    policy = RecordingAllowPolicy()
    scheduler = RetryingScheduler()
    controller = TrustedRunController(state_store=store, policy=policy)

    updated = controller.watch_run(
        task_id="task-auto-001",
        run_id="run-auto-001",
        scheduler=scheduler,
    )

    assert policy.actions == ["retry_transient_scheduler_failure"]
    assert len(scheduler.retry_calls) == 1
    assert updated.status == JobState.QUEUED
    assert updated.job_id == "67890"
    assert updated.auto_repair_attempts == 1
    assert updated.repeated_failures == 1
    assert updated.auto_continue_ready is False
    assert "retry" in updated.next_action.lower()
