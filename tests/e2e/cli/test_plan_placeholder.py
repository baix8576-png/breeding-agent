import json
from pathlib import Path

from typer.testing import CliRunner

from cli.app import app
from runtime.settings import get_settings

runner = CliRunner()


def test_cli_plan_command_returns_structured_plan_with_tracking_ids() -> None:
    result = runner.invoke(
        app,
        [
            "plan",
            "Run PCA on a sheep VCF dataset",
            "--task-id",
            "task-cli-plan-001",
            "--run-id",
            "run-cli-plan-001",
            "--working-directory",
            "/cluster/work/sheep",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["header"]["task_id"] == "task-cli-plan-001"
    assert payload["header"]["run_id"] == "run-cli-plan-001"
    assert payload["run_context"]["working_directory"] == "/cluster/work/sheep"
    assert payload["header"]["ready_for_gate"] == "design_pass"
    assert payload["workflow_name"] == "bioinformatics-standard-chain-v1"
    assert payload["pipeline_spec"]["name"] == "pca_pipeline"
    assert payload["domain"] == "bioinformatics"


def test_cli_plan_command_covers_non_bio_lightweight_branch() -> None:
    result = runner.invoke(
        app,
        [
            "plan",
            "Summarize local SOP checklist for troubleshooting",
            "--task-id",
            "task-cli-plan-knowledge-001",
            "--run-id",
            "run-cli-plan-knowledge-001",
            "--working-directory",
            "/cluster/work/sheep",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain"] == "knowledge"
    assert payload["workflow_name"] == "knowledge-lightweight-chain-v1"
    assert payload["pipeline_spec"]["name"] == "knowledge-lightweight-chain-v1"
    assert payload["pipeline_spec"]["blueprint_key"] is None


def test_cli_plan_command_accepts_input_bundle_entries(tmp_path: Path) -> None:
    vcf_path = tmp_path / "demo.vcf.gz"
    vcf_path.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "plan",
            "Run PCA on sheep cohort from explicit input bundle",
            "--task-id",
            "task-cli-plan-bundle-001",
            "--run-id",
            "run-cli-plan-bundle-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--input-entry",
            f"vcf={vcf_path}",
            "--input-species",
            "sheep",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["pipeline_spec"]["input_bundle"]["species"] == "sheep"
    assert payload["pipeline_spec"]["input_bundle"]["entries"][0]["role"] == "vcf"
    assert payload["input_validation"]["valid"] is True


def test_cli_report_command_returns_report_preview_payload() -> None:
    result = runner.invoke(
        app,
        [
            "report",
            "--task-id",
            "task-cli-report-001",
            "--run-id",
            "run-cli-report-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Generate report preview for sheep PCA outputs",
            "--requested-output",
            "structure_summary_report",
            "--requested-output",
            "pca_coordinates",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["run_context"]["task_id"] == "task-cli-report-001"
    assert payload["run_context"]["run_id"] == "run-cli-report-001"
    assert payload["cluster_execution_enabled"] is False
    assert isinstance(payload["selected_blueprint"], str)
    assert isinstance(payload["report_sections"], list)
    assert isinstance(payload["expected_artifacts"], dict)
    assert "reports" in payload["expected_artifacts"]


def test_cli_diagnostic_command_non_bio_branch_clearly_skips_cluster() -> None:
    result = runner.invoke(
        app,
        [
            "diagnostic",
            "--task-id",
            "task-cli-diagnostic-knowledge-001",
            "--run-id",
            "run-cli-diagnostic-knowledge-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Summarize local SOP troubleshooting checklist for report quality",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["run_context"]["task_id"] == "task-cli-diagnostic-knowledge-001"
    assert payload["cluster_execution_enabled"] is False
    assert isinstance(payload["fallback"], dict)
    assert payload["fallback"]["gate_decision"] in {"allowed", "blocked", "not_requested"}
    assert isinstance(payload["fallback"].get("gate_audit"), dict)
    assert "non_bio_cluster_policy" in payload
    assert "does not enter cluster execution" in payload["non_bio_cluster_policy"]


def test_cli_diagnostic_command_keeps_knowledge_fallback_path_for_low_coverage() -> None:
    result = runner.invoke(
        app,
        [
            "diagnostic",
            "--task-id",
            "task-cli-diagnostic-fallback-001",
            "--run-id",
            "run-cli-diagnostic-fallback-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "xqzv-404-zzzz",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain"] == "knowledge"
    assert payload["fallback_requested"] is True
    assert payload["fallback"]["requested"] is True
    assert payload["fallback"]["gate_decision"] in {"allowed", "blocked"}
    assert payload["fallback"]["gate_decision"] != "not_requested"
    assert isinstance(payload["fallback"]["gate_audit"], dict)
    assert "data_sensitivity_level" in payload["fallback"]["gate_audit"]
    assert payload["cluster_execution_enabled"] is False


def test_cli_dry_run_command_supports_pbs_scheduler_env() -> None:
    get_settings.cache_clear()
    try:
        result = runner.invoke(
            app,
            [
                "dry-run",
                "--task-id",
                "task-cli-dry-pbs-001",
                "--run-id",
                "run-cli-dry-pbs-001",
                "--working-directory",
                "/cluster/work/sheep",
                "--request-text",
                "Prepare a dry-run for PCA on sheep VCF under PBS",
            ],
            env={"GENEAGENT_SCHEDULER_TYPE": "pbs"},
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["cluster_execution_enabled"] is True
        assert payload["job_handle"]["scheduler"] == "pbs"
        assert payload["scheduler_script_path"].endswith(".pbs.sh")
        assert payload["polling_hint"].startswith("qstat -f ")
    finally:
        get_settings.cache_clear()


def test_cli_dry_run_command_returns_submission_preview() -> None:
    result = runner.invoke(
        app,
        [
            "dry-run",
            "--task-id",
            "task-cli-dry-001",
            "--run-id",
            "run-cli-dry-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Prepare a dry-run for PCA on sheep VCF",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["run_context"]["task_id"] == "task-cli-dry-001"
    assert payload["run_context"]["run_id"] == "run-cli-dry-001"
    assert payload["job_handle"]["run_context"]["task_id"] == "task-cli-dry-001"
    assert payload["job_handle"]["run_context"]["run_id"] == "run-cli-dry-001"
    assert payload["job_handle"]["state"] == "draft"
    assert payload["job_handle"]["job_id"].startswith("DRYRUN-SLURM-")
    assert payload["cluster_execution_enabled"] is True
    assert "# task_id: task-cli-dry-001" in payload["script_preview"]
    assert payload["wrapper_path"].endswith(".wrapper.sh")
    assert len(payload["poll_strategy"]) >= 3


def test_cli_dry_run_command_non_bio_branch_clearly_skips_cluster() -> None:
    result = runner.invoke(
        app,
        [
            "dry-run",
            "--task-id",
            "task-cli-dry-knowledge-001",
            "--run-id",
            "run-cli-dry-knowledge-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Summarize SOP guidance for cluster ticket templates",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["cluster_execution_enabled"] is False
    assert payload["scheduler_script_path"] is None
    assert payload["wrapper_path"] is None
    assert payload["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")
    assert payload["script_preview"].startswith("scheduler_skipped:")


def test_cli_submit_preview_command_returns_phase2_execution_surface() -> None:
    result = runner.invoke(
        app,
        [
            "submit-preview",
            "--task-id",
            "task-cli-submit-001",
            "--run-id",
            "run-cli-submit-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Submit preview for sheep PCA on VCF dataset",
            "--dry-run-completed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "submit-preview"
    assert payload["cluster_execution_enabled"] is True
    assert payload["run_context"]["task_id"] == "task-cli-submit-001"
    assert payload["job_handle"]["job_id"].startswith("PLAN-SLURM-")
    assert payload["scheduler_script_path"].endswith(".sbatch.sh")
    assert payload["wrapper_path"].endswith(".wrapper.sh")
    assert len(payload["failure_recovery"]) >= 3


def test_cli_submit_preview_command_non_bio_branch_clearly_skips_cluster() -> None:
    result = runner.invoke(
        app,
        [
            "submit-preview",
            "--task-id",
            "task-cli-submit-knowledge-001",
            "--run-id",
            "run-cli-submit-knowledge-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Summarize local SOP policy for report review",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "submit-preview"
    assert payload["cluster_execution_enabled"] is False
    assert payload["scheduler_script_path"] is None
    assert payload["wrapper_path"] is None
    assert payload["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")


def test_cli_submit_command_returns_submit_mode_payload() -> None:
    result = runner.invoke(
        app,
        [
            "submit",
            "--task-id",
            "task-cli-submit-real-001",
            "--run-id",
            "run-cli-submit-real-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Submit sheep PCA workflow now",
            "--dry-run-completed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "submit"
    assert payload["cluster_execution_enabled"] is True
    assert payload["job_handle"]["job_id"].startswith("PLAN-SLURM-")


def test_cli_submit_command_non_bio_branch_clearly_skips_cluster() -> None:
    result = runner.invoke(
        app,
        [
            "submit",
            "--task-id",
            "task-cli-submit-real-knowledge-001",
            "--run-id",
            "run-cli-submit-real-knowledge-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Summarize local SOP checklist for audit summaries",
            "--dry-run-completed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "submit"
    assert payload["cluster_execution_enabled"] is False
    assert payload["scheduler_script_path"] is None
    assert payload["job_handle"]["job_id"].startswith("SKIPPED-NONBIO-")


def test_cli_poll_explain_command_interprets_scheduler_state() -> None:
    result = runner.invoke(app, ["poll-explain", "SLURM-FAIL-TEST-001"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["job_id"] == "SLURM-FAIL-TEST-001"
    assert payload["state"] == "failed"
    assert payload["recommended_action"] == "trigger_failure_recovery"
    assert payload["terminal"] is True
