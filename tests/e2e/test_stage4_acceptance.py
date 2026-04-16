from __future__ import annotations

import json

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from api.app import create_app
from cli.app import app as cli_app


def test_stage4_acceptance_bio_has_dry_run_and_submit_paths() -> None:
    client = TestClient(create_app())
    dry_run = client.post(
        "/tasks/dry-run",
        json={
            "request_text": "Dry-run PCA on sheep VCF for acceptance gate",
            "identity": {
                "task_id": "task-stage4-bio-dry-001",
                "run_id": "run-stage4-bio-dry-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )
    submit = client.post(
        "/tasks/submit-preview",
        json={
            "request_text": "Submit preview PCA on sheep VCF for acceptance gate",
            "identity": {
                "task_id": "task-stage4-bio-submit-001",
                "run_id": "run-stage4-bio-submit-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert dry_run.status_code == 200
    assert submit.status_code == 200
    dry_payload = dry_run.json()["submission"]
    submit_payload = submit.json()["submission"]
    assert dry_payload["cluster_execution_enabled"] is True
    assert submit_payload["cluster_execution_enabled"] is True
    assert dry_payload["scheduler_script_path"] is not None
    assert submit_payload["scheduler_script_path"] is not None


def test_stage4_acceptance_non_bio_clearly_never_enters_cluster() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        [
            "submit-preview",
            "--task-id",
            "task-stage4-nonbio-001",
            "--run-id",
            "run-stage4-nonbio-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Summarize local SOP for audit review templates",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["cluster_execution_enabled"] is False
    assert payload["scheduler_script_path"] is None
    assert payload["wrapper_path"] is None
    assert payload["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")
    assert payload["script_preview"].startswith("scheduler_skipped:")


def test_stage4_acceptance_bio_submit_route_is_available() -> None:
    client = TestClient(create_app())

    submit = client.post(
        "/tasks/submit",
        json={
            "request_text": "Submit sheep PCA execution for acceptance gate",
            "dry_run_completed": True,
            "identity": {
                "task_id": "task-stage4-bio-submit-real-001",
                "run_id": "run-stage4-bio-submit-real-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert submit.status_code == 200
    payload = submit.json()["submission"]
    assert payload["mode"] == "submit"
    assert payload["cluster_execution_enabled"] is True
