from __future__ import annotations

from contracts.api import RequestIdentity
from runtime.bootstrap import create_application_context


def test_non_bio_dry_run_skips_scheduler_script_generation() -> None:
    context = create_application_context()

    submission = context.facade.build_dry_run_submission(
        request_text="Summarize local SOP checkpoints for data redaction",
        identity=RequestIdentity(
            task_id="task-runtime-knowledge-001",
            run_id="run-runtime-knowledge-001",
            working_directory="/cluster/work/sheep",
        ),
    )

    assert submission.run_context.task_id == "task-runtime-knowledge-001"
    assert submission.run_context.run_id == "run-runtime-knowledge-001"
    assert submission.cluster_execution_enabled is False
    assert submission.command == []
    assert submission.script_preview.startswith("scheduler_skipped:")
    assert submission.job_handle.job_id.startswith("SKIPPED-NONBIO-")
    assert submission.artifacts is not None
    assert "results" in submission.artifacts.artifact_index
    assert "reports" in submission.artifacts.artifact_index
    assert submission.artifacts.audit_record_path is not None
    assert submission.artifacts.memory_handoff_summary is not None


def test_bio_submit_preview_exposes_wrapper_poll_and_recovery_fields() -> None:
    context = create_application_context()

    submission = context.facade.build_submit_preview(
        request_text="Prepare submit preview for sheep PCA workflow",
        dry_run_completed=True,
        identity=RequestIdentity(
            task_id="task-runtime-submit-001",
            run_id="run-runtime-submit-001",
            working_directory="/cluster/work/sheep",
        ),
    )

    assert submission.mode == "submit-preview"
    assert submission.cluster_execution_enabled is True
    assert submission.run_context.task_id == "task-runtime-submit-001"
    assert submission.command[0] == "bash"
    assert submission.command[1].replace("\\", "/").endswith("scripts/pca_pipeline/run_pca_pipeline.sh")
    assert submission.scheduler_script_path is not None
    assert submission.scheduler_script_path.endswith(".sbatch.sh")
    assert submission.wrapper_path is not None
    assert submission.wrapper_path.endswith(".wrapper.sh")
    assert submission.wrapper_preview is not None
    assert "poll_hint:" in submission.wrapper_preview
    assert len(submission.poll_strategy) >= 3
    assert len(submission.failure_recovery) >= 3
    assert submission.job_handle.job_id.startswith("PLAN-SLURM-")
    assert submission.artifacts is not None
    assert "logs" in submission.artifacts.artifact_index
    assert len(submission.artifacts.artifact_index["logs"]) == 2
    assert submission.artifacts.report_summary is not None
    assert submission.artifacts.audit_record_path is not None
    assert submission.artifacts.memory_handoff_summary is not None


def test_poll_explanation_returns_structured_failed_state() -> None:
    context = create_application_context()

    poll = context.facade.explain_poll_state("SLURM-FAIL-EXAMPLE-001")

    assert poll.job_id == "SLURM-FAIL-EXAMPLE-001"
    assert poll.state.value == "failed"
    assert poll.recommended_action == "trigger_failure_recovery"
    assert poll.terminal is True


def test_bio_submit_returns_submit_mode_handle_when_real_execution_disabled() -> None:
    context = create_application_context()

    submission = context.facade.submit(
        request_text="Submit sheep PCA workflow for scheduler execution",
        dry_run_completed=True,
        identity=RequestIdentity(
            task_id="task-runtime-submit-real-001",
            run_id="run-runtime-submit-real-001",
            working_directory="/cluster/work/sheep",
        ),
    )

    assert submission.mode == "submit"
    assert submission.cluster_execution_enabled is True
    assert submission.command[0] == "bash"
    assert submission.job_handle.job_id.startswith("PLAN-SLURM-")
    assert submission.job_handle.state.value == "draft"
    assert submission.scheduler_script_path is not None
