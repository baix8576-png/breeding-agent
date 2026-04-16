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
    assert plan["workflow_name"] == "bioinformatics-standard-chain-v1"
    assert plan["pipeline_spec"]["name"] == "pca_pipeline"
    assert plan["pipeline_spec"]["blueprint_key"] == "pca"
    assert "pca_computation" in plan["pipeline_spec"]["stages"]
    assert "pca_computation" in plan["pipeline_spec"]["stage_contract"]
    assert len(plan["pipeline_spec"]["stage_io_contract"]) == 9


def test_tasks_draft_plan_route_covers_non_bio_lightweight_branch() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/draft-plan",
        json={
            "text": "Summarize local SOP for redaction-safe troubleshooting",
            "identity": {
                "task_id": "task-api-plan-knowledge-001",
                "run_id": "run-api-plan-knowledge-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    plan = response.json()["plan"]
    assert plan["domain"] == "knowledge"
    assert plan["workflow_name"] == "knowledge-lightweight-chain-v1"
    assert plan["pipeline_spec"]["name"] == "knowledge-lightweight-chain-v1"
    assert plan["pipeline_spec"]["blueprint_key"] is None
    assert len(plan["pipeline_spec"]["stage_io_contract"]) >= 3


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
    assert submission["cluster_execution_enabled"] is True
    assert "# task_id: task-api-dry-001" in submission["script_preview"]
    assert "# run_id: run-api-dry-001" in submission["script_preview"]
    assert submission["wrapper_path"].endswith(".wrapper.sh")
    assert "queued->running poll" in submission["wrapper_preview"]
    assert "artifact_index" in submission["artifacts"]
    assert "logs" in submission["artifacts"]["artifact_index"]
    assert submission["artifacts"]["audit_record_path"] is not None


def test_tasks_dry_run_route_non_bio_branch_clearly_skips_cluster() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/dry-run",
        json={
            "request_text": "Summarize SOP for genotype data governance checklist",
            "identity": {
                "task_id": "task-api-dry-knowledge-001",
                "run_id": "run-api-dry-knowledge-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["cluster_execution_enabled"] is False
    assert submission["scheduler_script_path"] is None
    assert submission["wrapper_path"] is None
    assert submission["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")
    assert submission["script_preview"].startswith("scheduler_skipped:")


def test_tasks_submit_preview_route_returns_phase2_execution_surface() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/submit-preview",
        json={
            "request_text": "Submit preview for sheep PCA on VCF panel",
            "dry_run_completed": True,
            "identity": {
                "task_id": "task-api-submit-001",
                "run_id": "run-api-submit-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["mode"] == "submit-preview"
    assert submission["cluster_execution_enabled"] is True
    assert submission["run_context"]["task_id"] == "task-api-submit-001"
    assert submission["job_handle"]["job_id"].startswith("PLAN-SLURM-")
    assert submission["scheduler_script_path"].endswith(".sbatch.sh")
    assert submission["wrapper_path"].endswith(".wrapper.sh")
    assert len(submission["poll_strategy"]) >= 3
    assert len(submission["failure_recovery"]) >= 3
    assert submission["gate_status"] in {"ready", "awaiting_confirmation", "blocked"}


def test_tasks_submit_preview_route_non_bio_branch_clearly_skips_cluster() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/submit-preview",
        json={
            "request_text": "Explain local documentation standards for audit summaries",
            "identity": {
                "task_id": "task-api-submit-knowledge-001",
                "run_id": "run-api-submit-knowledge-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["mode"] == "submit-preview"
    assert submission["cluster_execution_enabled"] is False
    assert submission["scheduler_script_path"] is None
    assert submission["wrapper_path"] is None
    assert submission["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")


def test_tasks_submit_route_returns_submit_mode_payload() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/submit",
        json={
            "request_text": "Submit sheep PCA workflow now",
            "dry_run_completed": True,
            "identity": {
                "task_id": "task-api-submit-real-001",
                "run_id": "run-api-submit-real-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["mode"] == "submit"
    assert submission["cluster_execution_enabled"] is True
    assert submission["job_handle"]["job_id"].startswith("PLAN-SLURM-")


def test_tasks_submit_route_non_bio_branch_stays_outside_cluster() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/submit",
        json={
            "request_text": "Summarize SOP for audit index maintenance",
            "dry_run_completed": True,
            "identity": {
                "task_id": "task-api-submit-real-knowledge-001",
                "run_id": "run-api-submit-real-knowledge-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 200
    submission = response.json()["submission"]
    assert submission["mode"] == "submit"
    assert submission["cluster_execution_enabled"] is False
    assert submission["scheduler_script_path"] is None
    assert submission["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")


def test_tasks_submit_route_blocks_dangerous_command_preview() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/submit",
        json={
            "request_text": "Run PCA on sheep VCF with dangerous command",
            "dry_run_completed": True,
            "command": ["rm", "-rf", "/tmp/geneagent"],
            "identity": {
                "task_id": "task-api-submit-real-blocked-001",
                "run_id": "run-api-submit-real-blocked-001",
                "working_directory": "/cluster/work/sheep",
            },
        },
    )

    assert response.status_code == 409
    assert "Safety gate rejected real submit" in response.json()["detail"]


def test_tasks_poll_explain_route_returns_structured_poll_interpretation() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/tasks/poll-explain",
        json={
            "job_id": "SLURM-RUN-TEST-001",
        },
    )

    assert response.status_code == 200
    poll = response.json()["poll"]
    assert poll["job_id"] == "SLURM-RUN-TEST-001"
    assert poll["state"] == "running"
    assert poll["recommended_action"] == "sleep_and_poll_again"
    assert poll["poll_command_hint"].startswith("squeue -j")
    assert poll["terminal"] is False


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


def test_tasks_validate_inputs_route_accepts_structured_bundle_payload(tmp_path) -> None:
    client = TestClient(create_app())
    vcf_path = tmp_path / "demo.vcf"
    phenotype_path = tmp_path / "demo_pheno.tsv"
    vcf_path.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")
    phenotype_path.write_text("sample_id\ttrait\nA\t1.2\n", encoding="utf-8")

    response = client.post(
        "/tasks/validate-inputs",
        json={
            "task_id": "task-api-val-structured-001",
            "run_id": "run-api-val-structured-001",
            "species": "sheep",
            "entries": [
                {"role": "vcf", "path": str(vcf_path)},
                {"role": "表型", "path": str(phenotype_path)},
            ],
        },
    )

    assert response.status_code == 200
    validation = response.json()["validation"]
    assert validation["valid"] is True
    assert validation["ready_for_gate"] == "ready_for_design"
    assert len(validation["normalized_inputs"]) == 2
    assert "vcf" in validation["detected_types"]
    assert any(check["check_id"] == "genotype_presence" for check in validation["consistency_checks"])
