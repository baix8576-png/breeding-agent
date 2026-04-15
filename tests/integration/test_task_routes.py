from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import create_app


def test_tasks_draft_plan_route_preserves_identity_and_pipeline_spec() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/draft-plan",
        json={
            "text": "Run PCA on a sheep VCF dataset",
            "identity": {
                "task_id": "task-api-plan-001",
                "run_id": "run-api-plan-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["header"]["task_id"] == "task-api-plan-001"
    assert plan["header"]["run_id"] == "run-api-plan-001"
    assert plan["run_context"]["task_id"] == "task-api-plan-001"
    assert plan["run_context"]["run_id"] == "run-api-plan-001"
    assert plan["run_context"]["working_directory"] == "/cluster/work/sheep"
    assert plan["header"]["ready_for_gate"] == "design_pass"
    assert plan["domain"] == "bioinformatics"
    assert plan["workflow_name"] == "bioinformatics-analysis-mvp"
    assert plan["pipeline_spec"]["name"] == "bioinformatics-analysis-mvp"


def test_tasks_dry_run_route_returns_submission_preview_and_job_handle() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/dry-run",
        json={
            "request_text": "Dry-run PCA on sheep VCF",
            "identity": {
                "task_id": "task-api-dry-001",
                "run_id": "run-api-dry-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["run_context"]["task_id"] == "task-api-dry-001"
    assert submission["run_context"]["run_id"] == "run-api-dry-001"
    assert submission["job_handle"]["run_context"]["task_id"] == "task-api-dry-001"
    assert submission["job_handle"]["run_context"]["run_id"] == "run-api-dry-001"
    assert submission["job_handle"]["state"] == "draft"
    assert submission["job_handle"]["job_id"].startswith("DRYRUN-SLURM-")
    assert "# task_id: task-api-dry-001" in submission["script_preview"]
    assert "# run_id: run-api-dry-001" in submission["script_preview"]


def test_tasks_review_action_route_returns_structured_gate() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/review-action",
        json={
            "action_name": "overwrite_results",
            "target_paths": ["/cluster/work/sheep/results"],
            "identity": {
                "task_id": "task-api-review-001",
                "run_id": "run-api-review-001",
            },
        },
    )

    assert response.status_code == 200
    review = response.json()["review"]
    assert review["task_id"] == "task-api-review-001"
    assert review["run_id"] == "run-api-review-001"
    assert review["ready_for_gate"] == "awaiting_confirmation"
    assert review["decision"] == "require_confirmation"
    assert review["risk_level"] == "manual_approval"


def test_tasks_validate_inputs_route_reports_missing_dataset() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/validate-inputs",
        json={"paths": ["missing_dataset.vcf"]},
    )

    assert response.status_code == 200
    validation = response.json()["validation"]
    assert validation["valid"] is False
    assert validation["issues"][0]["code"] == "missing_path"
