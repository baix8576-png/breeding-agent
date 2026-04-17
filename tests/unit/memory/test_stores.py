from __future__ import annotations

from contracts.common import TaskDomain
from memory import InMemoryRunStore, InMemorySessionStore, MemoryCoordinator, SessionRecord


def test_session_store_round_trip() -> None:
    store = InMemorySessionStore()
    record = SessionRecord(session_id="session-001", messages=["hello"], last_task_id="task-001")

    store.save(record)
    loaded = store.get("session-001")

    assert loaded is not None
    assert loaded.session_id == "session-001"
    assert loaded.messages == ["hello"]
    assert loaded.last_task_id == "task-001"


def test_memory_coordinator_plan_run_persists_handoffs() -> None:
    run_store = InMemoryRunStore()
    coordinator = MemoryCoordinator(run_store=run_store)

    record = coordinator.plan_run(
        task_id="task-memory-001",
        run_id="run-memory-001",
        session_id="session-memory-001",
        request_text="Draft a simple genetics workflow and preserve stage context.",
        domain=TaskDomain.BIOINFORMATICS,
        stage_specs=[
            {"stage_id": "stage_01_scope", "owner": "orchestrator", "outputs": ["scope_summary"]},
            {"stage_id": "stage_02_validate", "owner": "orchestrator", "outputs": ["validation_snapshot"]},
        ],
        available_tools=["input_validator"],
        retrieval_sources=["Input Compliance Checklist"],
    )

    loaded = run_store.get("run-memory-001")
    assert loaded is not None
    assert loaded.run_id == "run-memory-001"
    assert record.stage_history[0].stage_id == "stage_01_scope"
    assert record.stage_history[1].stage_id == "stage_02_validate"
    assert len(record.handoffs) == 1
    assert record.handoffs[0].from_stage == "stage_01_scope"
    assert record.handoffs[0].to_stage == "stage_02_validate"
    session = coordinator.get_session("session-memory-001")
    assert session is not None
    assert session.last_task_id == "task-memory-001"
    assert "run-memory-001" in session.run_ids


def test_memory_coordinator_records_execution_closure_for_run_and_session() -> None:
    run_store = InMemoryRunStore()
    session_store = InMemorySessionStore()
    coordinator = MemoryCoordinator(run_store=run_store, session_store=session_store)

    coordinator.plan_run(
        task_id="task-memory-closure-001",
        run_id="run-memory-closure-001",
        session_id="session-memory-closure-001",
        request_text="Prepare genomic prediction submission preview.",
        domain=TaskDomain.BIOINFORMATICS,
        stage_specs=[
            {"stage_id": "stage_07_execution", "owner": "hpc_scheduler", "outputs": ["submission_handle"]},
            {"stage_id": "stage_08_artifact_and_report", "owner": "popgen_quantgen", "outputs": ["report_index"]},
            {"stage_id": "stage_09_audit_and_memory", "owner": "orchestrator", "outputs": ["audit_record"]},
        ],
        available_tools=["scheduler_submission_preview"],
        retrieval_sources=["Pipeline SOP"],
    )

    record = coordinator.record_execution_closure(
        task_id="task-memory-closure-001",
        run_id="run-memory-closure-001",
        session_id="session-memory-closure-001",
        domain=TaskDomain.BIOINFORMATICS,
        input_summary="Prepare genomic prediction submission preview.",
        planning_summary="Bioinformatics workflow ready.",
        submission_command="sbatch /cluster/work/demo/.geneagent/scheduler/geneagent-job.sbatch.sh",
        job_id="PLAN-SLURM-task-memory-closure-001-run-memory-closure-001-GENEAGENT-JOB",
        log_paths=["/cluster/work/demo/logs/stdout.log", "/cluster/work/demo/logs/stderr.log"],
        manual_confirmation_records=["Cross-directory writes require scope confirmation."],
        artifact_index={
            "results": ["/cluster/work/demo/results/predictions.tsv"],
            "figures": [],
            "logs": ["/cluster/work/demo/logs/stdout.log", "/cluster/work/demo/logs/stderr.log"],
            "reports": ["/cluster/work/demo/reports/genomic_prediction_summary.md"],
        },
        report_summary="genomic_prediction 1 results, 0 figures, 2 logs, 1 reports indexed.",
        audit_path="/cluster/work/demo/.geneagent/audit/task-memory-closure-001/run-memory-closure-001.jsonl",
    )

    assert record.report_summary is not None
    assert "PLAN-SLURM-task-memory-closure-001" in record.job_ids[0]
    assert "sbatch /cluster/work/demo/.geneagent/scheduler/geneagent-job.sbatch.sh" in record.submission_commands
    assert len(record.log_paths) == 2
    assert len(record.audit_paths) == 1
    assert any(handoff.to_stage == "stage_09_audit_and_memory" for handoff in record.handoffs)
    session = coordinator.get_session("session-memory-closure-001")
    assert session is not None
    assert "execution_closure:run-memory-closure-001" in session.messages
