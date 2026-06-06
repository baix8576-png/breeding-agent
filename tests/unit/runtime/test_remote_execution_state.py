from __future__ import annotations

from pathlib import Path
import tempfile
from uuid import uuid4

from contracts.common import ExecutionMode, JobState, SchedulerKind
from contracts.remote_execution import RunStageRecord, RunState
from runtime.run_state import RunStateStore


def test_run_state_store_persists_local_state_not_remote_workdir(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")
    state = RunState(
        task_id="task-state-001",
        run_id="run-state-001",
        execution_mode=ExecutionMode.SSH_SLURM_TRUSTED,
        remote_profile_name="prod",
        scheduler=SchedulerKind.SLURM,
        working_directory="/cluster/work/alice/geneagent/run-state-001",
        current_stage="stage_07_execution",
        status=JobState.QUEUED,
        job_id="12345",
        auto_continue=True,
        stages=[
            RunStageRecord(
                stage_id="stage_07_execution",
                status="submitted",
                message="remote sbatch accepted",
            )
        ],
    )

    state_path = store.save(state)
    loaded = store.load(task_id="task-state-001", run_id="run-state-001")

    assert state_path == tmp_path / ".geneagent" / "runs" / "task-state-001" / "run-state-001" / "state.json"
    assert "/cluster/work" not in str(state_path).replace("\\", "/")
    assert loaded is not None
    assert loaded.job_id == "12345"
    assert loaded.execution_mode == ExecutionMode.SSH_SLURM_TRUSTED
    assert loaded.stages[0].stage_id == "stage_07_execution"


def test_run_state_store_latest_path_is_stable(tmp_path: Path) -> None:
    store = RunStateStore(root=tmp_path / ".geneagent")

    path = store.state_path(task_id="task-state-002", run_id="run-state-002")

    assert path == tmp_path / ".geneagent" / "runs" / "task-state-002" / "run-state-002" / "state.json"


def test_run_state_store_does_not_silently_fallback_when_primary_root_is_unwritable(tmp_path: Path) -> None:
    unique_suffix = uuid4().hex
    root = tmp_path / ".geneagent"
    (root / "runs").parent.mkdir(parents=True, exist_ok=True)
    (root / "runs").write_text("not a directory", encoding="utf-8")
    store = RunStateStore(root=root)
    state = RunState(
        task_id=f"task-state-unwritable-{unique_suffix}",
        run_id=f"run-state-unwritable-{unique_suffix}",
        execution_mode=ExecutionMode.SSH_SLURM_TRUSTED,
        remote_profile_name="prod",
        scheduler=SchedulerKind.SLURM,
        working_directory="/cluster/work/alice/geneagent/run-state-unwritable-001",
        status=JobState.QUEUED,
        job_id="12345",
    )

    try:
        store.save(state)
    except OSError:
        pass
    else:
        raise AssertionError("RunStateStore.save should fail when the configured state root is not writable.")

    cwd_fallback = Path.cwd() / ".tmp" / "geneagent_state" / "runs" / state.task_id / state.run_id / "state.json"
    temp_fallback = Path(tempfile.gettempdir()) / "geneagent_state" / "runs" / state.task_id / state.run_id / "state.json"
    assert not cwd_fallback.exists()
    assert not temp_fallback.exists()
