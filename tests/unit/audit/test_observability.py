from __future__ import annotations

from audit.observability import ObservabilityService
from audit.store import AuditEvent, FileAuditStore


def test_observability_service_aggregates_runtime_scheduler_and_failure_metrics(tmp_path) -> None:
    store = FileAuditStore(fallback_root=str(tmp_path / "audit_fallback"))
    service = ObservabilityService(store)
    workdir = tmp_path / "work"
    event = AuditEvent(
        task_id="task-obs-001",
        run_id="run-obs-001",
        event_type="execution_closure",
        stage_id="stage_09_audit_and_memory",
        summary="submit execution closure recorded for task/run context.",
        metadata={
            "job_id": "PLAN-SLURM-task-obs-001-run-obs-001-GENEAGENT-JOB",
            "report_summary": "pca_pipeline selected; diagnostics=failed. report_generator_status=integrated.",
            "runtime_lifecycle": {"runtime_path": "bio_main_chain", "current_stage": "completed"},
            "manual_confirmation_records": ["approve overwrite before submit"],
            "artifact_index": {"reports": ["reports/summary_report.md"]},
            "input_summary": "run pca",
            "planning_summary": "plan built",
            "submission_command": "sbatch .geneagent/scheduler/demo.sbatch.sh",
            "log_paths": ["logs/stdout.log", "logs/stderr.log"],
        },
    )
    store.append(event, working_directory=str(workdir))

    metrics = service.build_metrics(working_directory=str(workdir), limit=10)

    assert metrics["schema_version"] == "observability_metrics.v1"
    assert metrics["task_metrics"]["total_runs"] == 1
    assert metrics["task_metrics"]["runtime_paths"]["bio_main_chain"] == 1
    assert metrics["scheduler_metrics"]["scheduler_distribution"]["slurm"] == 1
    assert metrics["failure_taxonomy"]["classes"]["execution_failed"] == 1


def test_observability_dashboard_contains_board_and_top_failures(tmp_path) -> None:
    store = FileAuditStore(fallback_root=str(tmp_path / "audit_fallback"))
    service = ObservabilityService(store)
    workdir = tmp_path / "work"
    store.append(
        AuditEvent(
            task_id="task-obs-002",
            run_id="run-obs-002",
            event_type="execution_closure",
            summary="dry-run execution closure recorded for task/run context.",
            metadata={
                "job_id": "DRYRUN-SLURM-task-obs-002-run-obs-002-GENEAGENT-JOB",
                "report_summary": "qc_pipeline selected; diagnostics=ok.",
                "runtime_lifecycle": {"runtime_path": "bio_main_chain", "current_stage": "completed"},
                "input_summary": "run qc",
                "planning_summary": "plan built",
                "submission_command": "sbatch demo.sbatch.sh",
                "log_paths": [],
                "manual_confirmation_records": [],
            },
        ),
        working_directory=str(workdir),
    )

    dashboard = service.build_dashboard(working_directory=str(workdir), limit=10)

    assert dashboard["schema_version"] == "observability_dashboard.v1"
    assert isinstance(dashboard["board"], list)
    assert isinstance(dashboard["top_failure_classes"], list)
