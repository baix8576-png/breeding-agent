from __future__ import annotations

from pathlib import Path

from audit import AuditEvent, FileAuditStore, InMemoryAuditStore


def test_audit_store_append_and_list() -> None:
    store = InMemoryAuditStore()

    store.append(
        AuditEvent(
            task_id="task-audit-001",
            run_id="run-audit-001",
            event_type="plan_drafted",
            summary="Draft plan created in dry-run mode.",
        )
    )

    events = store.list_events()
    assert len(events) == 1
    assert events[0].event_type == "plan_drafted"
    assert events[0].task_id == "task-audit-001"
    assert events[0].schema_version == "audit_event.v2"


def test_audit_store_list_returns_copy() -> None:
    store = InMemoryAuditStore()
    store.append(
        AuditEvent(
            task_id="task-audit-002",
            run_id="run-audit-002",
            event_type="gate_checked",
            summary="Safety gate was checked.",
        )
    )

    snapshot = store.list_events()
    snapshot.append(
        AuditEvent(
            task_id="task-audit-003",
            run_id="run-audit-003",
            event_type="external_mutation",
            summary="Should not change the internal store.",
        )
    )

    assert len(store.list_events()) == 1


def test_file_audit_store_persists_jsonl_records(tmp_path) -> None:
    store = FileAuditStore(fallback_root=str(tmp_path / "audit_fallback"))
    event = AuditEvent(
        task_id="task-audit-file-001",
        run_id="run-audit-file-001",
        event_type="execution_closure",
        summary="Persist audit closure record.",
        metadata={
            "submission_command": "sbatch /tmp/script.sh",
            "job_id": "PLAN-SLURM-task-audit-file-001-run-audit-file-001-GENEAGENT-JOB",
            "log_paths": ["/tmp/stdout.log", "/tmp/stderr.log"],
        },
    )

    file_path = store.append(event, working_directory=str(tmp_path / "work"))

    assert file_path is not None
    assert Path(file_path).exists()
    lines = Path(file_path).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert store.resolve_run_file("task-audit-file-001", "run-audit-file-001") == file_path


def test_file_audit_store_can_read_run_events_and_board_snapshot(tmp_path) -> None:
    store = FileAuditStore(fallback_root=str(tmp_path / "audit_fallback"))
    workdir = tmp_path / "work"
    event = AuditEvent(
        task_id="task-audit-file-002",
        run_id="run-audit-file-002",
        event_type="execution_closure",
        stage_id="stage_09_audit_and_memory",
        summary="Closure event persisted.",
        metadata={
            "job_id": "PLAN-SLURM-task-audit-file-002-run-audit-file-002-GENEAGENT-JOB",
            "report_summary": "QC summary generated.",
            "runtime_lifecycle": {"runtime_path": "bio_main_chain", "current_stage": "completed"},
            "artifact_index": {"reports": ["reports/summary_report.md"]},
        },
    )
    file_path = store.append(event, working_directory=str(workdir))

    events, resolved = store.read_run_events(
        run_id="run-audit-file-002",
        task_id="task-audit-file-002",
        working_directory=str(workdir),
    )

    assert file_path is not None
    assert resolved == file_path
    assert len(events) == 1
    assert events[0].event_type == "execution_closure"

    board = store.list_recent_runs(working_directory=str(workdir), limit=5)
    assert len(board) == 1
    assert board[0]["task_id"] == "task-audit-file-002"
    assert board[0]["run_id"] == "run-audit-file-002"
    assert board[0]["runtime_path"] == "bio_main_chain"
