from __future__ import annotations

import subprocess

from contracts.tasks import ResourceEstimate
from scheduler.pbs import PbsSchedulerAdapter
from scheduler.poller import JobPoller
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


