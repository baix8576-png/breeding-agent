import json

from typer.testing import CliRunner

from cli.app import app

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
    assert payload["workflow_name"] == "bioinformatics-analysis-mvp"
    assert payload["domain"] == "bioinformatics"


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
    assert "# task_id: task-cli-dry-001" in payload["script_preview"]
