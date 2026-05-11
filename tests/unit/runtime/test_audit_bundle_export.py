from __future__ import annotations

import json
from pathlib import Path

from contracts.api import RequestIdentity
from runtime.bootstrap import create_application_context


def test_export_audit_bundle_emits_zip_and_manifest(tmp_path: Path) -> None:
    context = create_application_context()
    task_id = "task-runtime-audit-export-001"
    run_id = "run-runtime-audit-export-001"
    submission = context.facade.build_dry_run_submission(
        request_text="Dry-run PCA for audit export test",
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            working_directory=str(tmp_path),
        ),
    )
    assert submission.artifacts is not None
    assert submission.artifacts.audit_record_path is not None

    exported = context.facade.export_audit_bundle(
        run_id=run_id,
        task_id=task_id,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            working_directory=str(tmp_path),
        ),
        include_files=True,
    )

    bundle_path = Path(exported.bundle_path)
    manifest_path = Path(exported.manifest_path)
    assert bundle_path.is_file()
    assert bundle_path.suffix == ".zip"
    assert manifest_path.is_file()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "audit_bundle.v1"
    assert payload["run_context"]["task_id"] == task_id
    assert payload["run_context"]["run_id"] == run_id
    assert "input" in payload
    assert "plan" in payload
    assert "execution" in payload
    assert "logs" in payload
    assert "report" in payload
    assert "approval_trail" in payload


def test_run_snapshot_can_be_loaded_from_persisted_audit_without_memory_state(tmp_path: Path) -> None:
    task_id = "task-runtime-audit-export-002"
    run_id = "run-runtime-audit-export-002"
    context_a = create_application_context()
    context_a.facade.build_submit_preview(
        request_text="Submit preview for audit snapshot loading",
        dry_run_completed=True,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            working_directory=str(tmp_path),
        ),
    )

    # New context simulates a fresh process without in-memory run state.
    context_b = create_application_context()
    snapshot = context_b.facade.get_run_snapshot(
        run_id=run_id,
        task_id=task_id,
        working_directory=str(tmp_path),
    )

    assert snapshot["run_context"]["task_id"] == task_id
    assert snapshot["run_context"]["run_id"] == run_id
    assert snapshot["audit_event_count"] >= 1
    assert isinstance(snapshot["submission_commands"], list)
    assert isinstance(snapshot["job_ids"], list)
