from __future__ import annotations

from contracts.tasks import ResourceEstimate
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
    assert plan.polling_hint is not None
    assert "squeue -j" in plan.polling_hint


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


