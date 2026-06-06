from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import time

from contracts.api import RequestIdentity
from contracts.tasks import ResourceEstimate
from runtime.bootstrap import create_application_context
from scheduler.slurm import SlurmSchedulerAdapter


def test_concurrent_dry_run_submit_preview_and_submit_stability(tmp_path: Path) -> None:
    def worker(index: int) -> tuple[str, str, str, bool]:
        context = create_application_context()
        workdir = tmp_path / f"run_{index:03d}"
        workdir.mkdir(parents=True, exist_ok=True)
        dry_run = context.facade.build_dry_run_submission(
            request_text=f"Dry-run PCA concurrent task {index}",
            identity=RequestIdentity(
                task_id=f"task-perf-dry-{index:03d}",
                run_id=f"run-perf-dry-{index:03d}",
                working_directory=str(workdir),
            ),
        )
        preview = context.facade.build_submit_preview(
            request_text=f"Submit preview PCA concurrent task {index}",
            dry_run_completed=True,
            identity=RequestIdentity(
                task_id=f"task-perf-preview-{index:03d}",
                run_id=f"run-perf-preview-{index:03d}",
                working_directory=str(workdir),
            ),
        )
        submit = context.facade.submit(
            request_text=f"Submit PCA concurrent task {index}",
            dry_run_completed=True,
            identity=RequestIdentity(
                task_id=f"task-perf-submit-{index:03d}",
                run_id=f"run-perf-submit-{index:03d}",
                working_directory=str(workdir),
            ),
        )
        return (
            dry_run.job_handle.job_id,
            preview.job_handle.job_id,
            submit.job_handle.job_id,
            submit.cluster_execution_enabled,
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        outputs = list(pool.map(worker, range(12)))

    assert len(outputs) == 12
    assert all(item[3] is True for item in outputs)
    assert all(job_id.startswith("DRYRUN-") for job_id, _preview_id, _submit_id, _enabled in outputs)
    assert all(preview_id.startswith("PLAN-") for _job_id, preview_id, _submit_id, _enabled in outputs)
    assert all(submit_id.startswith("PLAN-") for _job_id, _preview_id, submit_id, _enabled in outputs)


def test_long_poll_loop_stability() -> None:
    context = create_application_context()
    started = time.perf_counter()
    states = []
    for index in range(1200):
        if index % 4 == 0:
            job_id = f"SLURM-QUEUED-LONG-{index}"
        elif index % 4 == 1:
            job_id = f"SLURM-RUN-LONG-{index}"
        elif index % 4 == 2:
            job_id = f"SLURM-DONE-LONG-{index}"
        else:
            job_id = f"SLURM-FAIL-LONG-{index}"
        states.append(context.facade.explain_poll_state(job_id).state.value)
    elapsed = time.perf_counter() - started

    assert len(states) == 1200
    assert {"queued", "running", "completed", "failed"}.issubset(set(states))
    assert elapsed < 6.0


def test_scheduler_retry_recovery_path_succeeds_after_transient_failure(tmp_path: Path) -> None:
    attempts = {"count": 0}

    def flaky_runner(command: list[str], cwd: str | None, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
        _ = (cwd, timeout_seconds)
        attempts["count"] += 1
        if attempts["count"] == 1:
            return subprocess.CompletedProcess(command, returncode=1, stdout="", stderr="temporary scheduler error")
        return subprocess.CompletedProcess(command, returncode=0, stdout="Submitted batch job 556677", stderr="")

    adapter = SlurmSchedulerAdapter(
        real_execution_enabled=True,
        retry_max_attempts=3,
        retry_backoff_seconds=[0, 0, 0],
        command_runner=flaky_runner,
    )
    workdir = tmp_path / "scheduler_recovery"
    workdir.mkdir(parents=True, exist_ok=True)
    handle = adapter.submit(
        working_directory=str(workdir),
        resources=ResourceEstimate(cpus=4, memory_gb=16, walltime="02:00:00"),
        command=["bash", "scripts/population_genetics/run_population_structure_diversity.sh"],
        task_id="task-perf-retry-001",
        run_id="run-perf-retry-001",
    )

    assert handle.job_id == "556677"
    assert handle.state.value == "queued"
    assert attempts["count"] >= 2
