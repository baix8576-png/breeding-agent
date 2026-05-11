from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app


def test_v2_tasks_route_returns_stable_version_headers() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/v2/tasks/draft-plan",
        json={
            "text": "Run PCA on sheep VCF",
            "identity": {
                "task_id": "task-api-v2-plan-001",
                "run_id": "run-api-v2-plan-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    assert response.headers["X-GeneAgent-API-Version"] == "v2"
    assert response.headers["X-GeneAgent-Stability"] == "stable"


def test_v1_tasks_route_exposes_deprecation_headers() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/tasks/draft-plan",
        json={
            "text": "Run PCA on sheep VCF",
            "identity": {
                "task_id": "task-api-v1-plan-001",
                "run_id": "run-api-v1-plan-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    assert response.headers["X-GeneAgent-API-Version"] == "v1"
    assert response.headers["Deprecation"] == "true"
    assert response.headers["Sunset"] == "2026-11-09"


def test_v2_version_policy_endpoint_returns_compatibility_window() -> None:
    client = TestClient(create_app())

    response = client.get("/v2/version-policy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "api_version_policy.v1"
    assert payload["current_api_version"] == "v2"
    assert payload["stable_prefix"] == "/v2/tasks"
    assert payload["legacy_prefix"] == "/tasks"
    assert payload["compatibility_window_days"] == 180


def test_v2_audit_export_route_emits_bundle(tmp_path: Path) -> None:
    client = TestClient(create_app())
    task_id = "task-api-v2-audit-001"
    run_id = "run-api-v2-audit-001"
    dry_run = client.post(
        "/v2/tasks/dry-run",
        json={
            "request_text": "Dry-run PCA for API audit export",
            "identity": {
                "task_id": task_id,
                "run_id": run_id,
                "working_directory": str(tmp_path),
            },
        },
    )
    assert dry_run.status_code == 200

    exported = client.post(
        "/v2/tasks/audit-export",
        json={
            "run_id": run_id,
            "task_id": task_id,
            "identity": {
                "task_id": task_id,
                "run_id": run_id,
                "working_directory": str(tmp_path),
            },
        },
    )
    assert exported.status_code == 200
    bundle = exported.json()["audit_bundle"]
    assert Path(bundle["bundle_path"]).is_file()
    assert Path(bundle["manifest_path"]).is_file()
    assert bundle["run_context"]["task_id"] == task_id
    assert bundle["run_context"]["run_id"] == run_id


def test_v2_console_board_and_run_snapshot(tmp_path: Path) -> None:
    client = TestClient(create_app())
    task_id = "task-api-v2-console-001"
    run_id = "run-api-v2-console-001"
    dry_run = client.post(
        "/v2/tasks/dry-run",
        json={
            "request_text": "Dry-run PCA for console board",
            "identity": {
                "task_id": task_id,
                "run_id": run_id,
                "working_directory": str(tmp_path),
            },
        },
    )
    assert dry_run.status_code == 200

    board = client.get("/v2/console/board", params={"working_directory": str(tmp_path), "limit": 20})
    assert board.status_code == 200
    runs = board.json()["board"]["runs"]
    assert any(item["run_id"] == run_id for item in runs)

    snapshot = client.get(
        f"/v2/console/runs/{run_id}",
        params={"task_id": task_id, "working_directory": str(tmp_path)},
    )
    assert snapshot.status_code == 200
    run = snapshot.json()["run"]
    assert run["run_context"]["task_id"] == task_id
    assert run["run_context"]["run_id"] == run_id
    assert isinstance(run["artifact_index"], dict)


def test_v2_console_home_renders_html() -> None:
    client = TestClient(create_app())

    response = client.get("/v2/console")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "GeneAgent V2 Console" in response.text


def test_v2_observability_metrics_and_dashboard_routes(tmp_path: Path) -> None:
    client = TestClient(create_app())
    task_id = "task-api-v2-observe-001"
    run_id = "run-api-v2-observe-001"
    dry_run = client.post(
        "/v2/tasks/dry-run",
        json={
            "request_text": "Dry-run PCA for observability metrics",
            "identity": {
                "task_id": task_id,
                "run_id": run_id,
                "working_directory": str(tmp_path),
            },
        },
    )
    assert dry_run.status_code == 200

    metrics = client.get("/v2/observability/metrics", params={"working_directory": str(tmp_path), "limit": 100})
    assert metrics.status_code == 200
    metrics_payload = metrics.json()["metrics"]
    assert metrics_payload["schema_version"] == "observability_metrics.v1"
    assert "task_metrics" in metrics_payload

    dashboard = client.get("/v2/observability/dashboard", params={"working_directory": str(tmp_path), "limit": 100})
    assert dashboard.status_code == 200
    dashboard_payload = dashboard.json()["dashboard"]
    assert dashboard_payload["schema_version"] == "observability_dashboard.v1"
    assert isinstance(dashboard_payload["board"], list)


def test_v2_release_endpoints_cover_gate_plan_release_template_and_final_review(tmp_path: Path) -> None:
    client = TestClient(create_app())

    gate = client.post(
        "/v2/release/production-gate",
        json={
            "working_directory": str(tmp_path),
            "execute_tests": False,
            "timeout_seconds": 120,
        },
    )
    assert gate.status_code == 200
    gate_payload = gate.json()["production_gate"]
    assert gate_payload["schema_version"] == "production_gate.v1"
    assert gate_payload["overall_status"] in {"planned", "pass"}

    plan = client.post(
        "/v2/release/plan",
        json={
            "version_tag": "v2.0.0-rc1",
            "change_summary": "Stabilize explanation layer and observability outputs.",
            "stage_ids": ["stage_05_blueprint_selection", "stage_06_resource_and_safety_gate"],
        },
    )
    assert plan.status_code == 200
    plan_payload = plan.json()["release_plan"]
    assert plan_payload["schema_version"] == "release_plan.v1"
    assert plan_payload["version_tag"] == "v2.0.0-rc1"
    assert plan_payload["rollback_plan"]

    review = client.get("/v2/release/final-review")
    assert review.status_code == 200
    review_payload = review.json()["final_review"]
    assert review_payload["schema_version"] == "v2_final_review.v1"
    assert review_payload["overall_status"] in {"pass", "not_ready"}
