from __future__ import annotations

import subprocess

import pytest

from contracts.tasks import ResourceEstimate
from scheduler.pbs import PbsSchedulerAdapter
from scheduler.poller import JobPoller
from scheduler.base import SchedulerExecutionError
from scheduler.slurm import SlurmSchedulerAdapter


def test_slurm_submission_plan_returns_structured_dry_run_metadata() -> None:
    adapter = SlurmSchedulerAdapter()

    plan = adapter.build_submission_plan(
        command=["bash", "scripts/pca_pipeline/run_pca.sh"],
        working_directory="/cluster/work/demo",
        resources=ResourceEstimate(cpus=8, memory_gb=24, walltime="02:30:00"),
        task_id="task-scheduler-001",
        run_id="run-scheduler-001",
    )

    assert plan.task_id == "task-scheduler-001"
    assert plan.run_id == "run-scheduler-001"
    assert plan.ready_for_gate == "scheduler_plan_ready"
    assert plan.job_handle.run_context.task_id == "task-scheduler-001"
    assert plan.job_handle.run_context.run_id == "run-scheduler-001"
    assert plan.job_handle.state.value == "draft"
    assert "task-scheduler-001" in plan.job_handle.job_id
    assert "run-scheduler-001" in plan.job_handle.job_id
    assert "# task_id: task-scheduler-001" in plan.script_preview
    assert "# run_id: run-scheduler-001" in plan.script_preview
    assert "#SBATCH --cpus-per-task=8" in plan.script_preview
    assert "#SBATCH --mem=24G" in plan.script_preview
    assert plan.submit_command == ["sbatch", "/cluster/work/demo/.geneagent/scheduler/geneagent-job.sbatch.sh"]
    assert plan.paths.wrapper_path.endswith(".wrapper.sh")
    assert "mode: dry-run" in plan.wrapper_preview
    assert "poll_hint:" in plan.wrapper_preview
    assert plan.polling_hint is not None
    assert "squeue -j" in plan.polling_hint
    assert len(plan.poll_strategy) >= 3
    assert len(plan.failure_recovery) >= 3


def test_scheduler_poller_interprets_dry_run_handle_as_review_step() -> None:
    adapter = SlurmSchedulerAdapter()
    handle = adapter.dry_run_submit(
        working_directory="/cluster/work/demo",
        resources=ResourceEstimate(),
        task_id="task-scheduler-002",
        run_id="run-scheduler-002",
    )

    explanation = JobPoller().explain_handle(handle)

    assert explanation.state.value == "draft"
    assert explanation.recommended_action == "review_plan_before_submission"
    assert explanation.terminal is False
    assert "planning mode" in explanation.explanation


def test_slurm_real_submit_retries_and_parses_job_id(tmp_path) -> None:
    submit_attempts = 0

    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        nonlocal submit_attempts
        _ = (cwd, timeout)
        if command[0] == "sbatch":
            submit_attempts += 1
            if submit_attempts == 1:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="transient scheduler issue")
            return subprocess.CompletedProcess(command, 0, stdout="Submitted batch job 812345\n", stderr="")
        raise AssertionError(f"Unexpected command: {command}")

    adapter = SlurmSchedulerAdapter(
        real_execution_enabled=True,
        retry_max_attempts=2,
        retry_backoff_seconds=[0],
        command_runner=command_runner,
    )

    handle = adapter.submit(
        working_directory=str(tmp_path),
        resources=ResourceEstimate(cpus=4, memory_gb=8, walltime="01:00:00"),
        task_id="task-slurm-submit-001",
        run_id="run-slurm-submit-001",
    )

    assert submit_attempts == 2
    assert handle.job_id == "812345"
    assert handle.state.value == "queued"
    assert handle.stdout_path is not None
    assert handle.stderr_path is not None


def test_slurm_real_poll_uses_squeue_then_sacct_fallback() -> None:
    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        _ = (cwd, timeout)
        if command[0] == "squeue":
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        if command[0] == "sacct":
            return subprocess.CompletedProcess(command, 0, stdout="COMPLETED\n", stderr="")
        raise AssertionError(f"Unexpected command: {command}")

    adapter = SlurmSchedulerAdapter(real_execution_enabled=True, command_runner=command_runner)

    state = adapter.poll("812345")

    assert state.value == "completed"


def test_pbs_real_submit_and_poll_parse_job_state(tmp_path) -> None:
    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        _ = (cwd, timeout)
        if command[0] == "qsub":
            return subprocess.CompletedProcess(command, 0, stdout="4123.server\n", stderr="")
        if command[0] == "qstat":
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="Job Id: 4123.server\n    job_state = F\n    Exit_status = 0\n",
                stderr="",
            )
        raise AssertionError(f"Unexpected command: {command}")

    adapter = PbsSchedulerAdapter(real_execution_enabled=True, command_runner=command_runner)

    handle = adapter.submit(
        working_directory=str(tmp_path),
        resources=ResourceEstimate(cpus=4, memory_gb=8, walltime="01:00:00"),
        task_id="task-pbs-submit-001",
        run_id="run-pbs-submit-001",
    )
    state = adapter.poll(handle.job_id)

    assert handle.job_id == "4123.server"
    assert state.value == "completed"


def test_pbs_real_submit_retries_transient_error_then_succeeds(tmp_path) -> None:
    submit_attempts = 0

    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        nonlocal submit_attempts
        _ = (cwd, timeout)
        if command[0] == "qsub":
            submit_attempts += 1
            if submit_attempts == 1:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="cannot connect to server")
            return subprocess.CompletedProcess(command, 0, stdout="5123.server\n", stderr="")
        raise AssertionError(f"Unexpected command: {command}")

    adapter = PbsSchedulerAdapter(
        real_execution_enabled=True,
        retry_max_attempts=2,
        retry_backoff_seconds=[0],
        command_runner=command_runner,
    )

    handle = adapter.submit(
        working_directory=str(tmp_path),
        resources=ResourceEstimate(cpus=2, memory_gb=4, walltime="00:30:00"),
        task_id="task-pbs-retry-001",
        run_id="run-pbs-retry-001",
    )

    assert submit_attempts == 2
    assert handle.job_id == "5123.server"
    assert handle.state.value == "queued"


def test_pbs_real_submit_permission_denied_is_not_retried(tmp_path) -> None:
    submit_attempts = 0

    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        nonlocal submit_attempts
        _ = (cwd, timeout)
        if command[0] == "qsub":
            submit_attempts += 1
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="qsub: Unauthorized Request")
        raise AssertionError(f"Unexpected command: {command}")

    adapter = PbsSchedulerAdapter(
        real_execution_enabled=True,
        retry_max_attempts=3,
        retry_backoff_seconds=[0],
        command_runner=command_runner,
    )

    with pytest.raises(SchedulerExecutionError) as raised:
        adapter.submit(
            working_directory=str(tmp_path),
            resources=ResourceEstimate(cpus=2, memory_gb=4, walltime="00:30:00"),
            task_id="task-pbs-denied-001",
            run_id="run-pbs-denied-001",
        )

    assert submit_attempts == 1
    assert raised.value.command[0] == "qsub"
    assert raised.value.error_code == "SUBMIT_PERMISSION_DENIED"
    assert raised.value.attempts == 1


def test_pbs_real_poll_uses_qstat_f_then_xf_fallback() -> None:
    commands: list[list[str]] = []

    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        _ = (cwd, timeout)
        commands.append(command)
        if command[:2] == ["qstat", "-f"]:
            return subprocess.CompletedProcess(command, 153, stdout="", stderr="qstat: Unknown Job Id 4123.server")
        if command[:2] == ["qstat", "-xf"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="Job Id: 4123.server\n    job_state = F\n    Exit_status = 0\n",
                stderr="",
            )
        raise AssertionError(f"Unexpected command: {command}")

    adapter = PbsSchedulerAdapter(real_execution_enabled=True, command_runner=command_runner)
    state = adapter.poll("4123.server")

    assert state.value == "completed"
    assert commands[0][:2] == ["qstat", "-f"]
    assert commands[1][:2] == ["qstat", "-xf"]


def test_pbs_real_poll_non_unknown_job_error_returns_unknown() -> None:
    commands: list[list[str]] = []

    def command_runner(command: list[str], cwd: str | None, timeout: int) -> subprocess.CompletedProcess[str]:
        _ = (cwd, timeout)
        commands.append(command)
        if command[:2] == ["qstat", "-f"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="qstat: permission denied")
        raise AssertionError(f"Unexpected command: {command}")

    adapter = PbsSchedulerAdapter(real_execution_enabled=True, command_runner=command_runner)
    state = adapter.poll("4123.server")

    assert state.value == "unknown"
    assert commands == [["qstat", "-f", "4123.server"]]


@pytest.mark.parametrize(
    ("token", "output", "expected_state"),
    [
        ("Q", "job_state = Q\n", "queued"),
        ("R", "job_state = R\n", "running"),
        ("F", "job_state = F\nExit_status = 0\n", "completed"),
        ("F", "job_state = F\nExit_status = 1\n", "failed"),
        ("F", "job_state = F\n", "unknown"),
        ("X", "job_state = X\n", "failed"),
        ("Z", "job_state = Z\n", "unknown"),
    ],
)
def test_pbs_state_parsing_maps_tokens_and_exit_status(token: str, output: str, expected_state: str) -> None:
    adapter = PbsSchedulerAdapter()
    assert adapter._state_from_pbs_token(token, output).value == expected_state


def test_pbs_submission_plan_recovery_text_is_consistent_with_slurm() -> None:
    resources = ResourceEstimate(cpus=4, memory_gb=8, walltime="01:00:00")
    pbs_plan = PbsSchedulerAdapter().build_submission_plan(
        command=["echo", "pbs"],
        working_directory="/cluster/work/demo",
        resources=resources,
        task_id="task-pbs-plan-001",
        run_id="run-pbs-plan-001",
    )
    slurm_plan = SlurmSchedulerAdapter().build_submission_plan(
        command=["echo", "slurm"],
        working_directory="/cluster/work/demo",
        resources=resources,
        task_id="task-slurm-plan-001",
        run_id="run-slurm-plan-001",
    )

    assert pbs_plan.polling_hint is not None
    assert "qstat -f" in pbs_plan.polling_hint
    assert any("auto retry strategy" in line for line in pbs_plan.failure_recovery)
    assert any("require manual approval before requeue" in line for line in pbs_plan.failure_recovery)
    assert any("auto retry strategy" in line for line in slurm_plan.failure_recovery)
    assert any("require manual approval before requeue" in line for line in slurm_plan.failure_recovery)


def test_default_command_runner_uses_windows_cmd_fallback(monkeypatch) -> None:
    adapter = SlurmSchedulerAdapter()
    invocations: list[list[str]] = []

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        invocations.append(command)
        if command[0] == "sbatch":
            raise FileNotFoundError("sbatch missing in PATH")
        return subprocess.CompletedProcess(command, 0, stdout="Submitted batch job 1001\n", stderr="")

    monkeypatch.setattr(adapter, "_is_windows_runtime", lambda: True)
    monkeypatch.setattr("scheduler.base.shutil.which", lambda name: r"C:\shim\sbatch.cmd" if name == "sbatch.cmd" else None)
    monkeypatch.setattr("scheduler.base.subprocess.run", fake_run)

    result = adapter._default_command_runner(["sbatch", "demo.sbatch.sh"], cwd=None, timeout_seconds=3)

    assert result.returncode == 0
    assert invocations[0][0] == "sbatch"
    assert invocations[1][0].lower().endswith("sbatch.cmd")


def test_run_command_error_message_includes_missing_executable_name() -> None:
    def missing_runner(_command: list[str], _cwd: str | None, _timeout: int) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("not found")

    adapter = SlurmSchedulerAdapter(command_runner=missing_runner)

    with pytest.raises(SchedulerExecutionError) as raised:
        adapter._run_command(command=["sbatch", "demo.sbatch.sh"], cwd=None, timeout_seconds=2)

    assert "sbatch" in str(raised.value)


