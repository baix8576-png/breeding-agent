from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from cli.app import app
from runtime.settings import get_settings


runner = CliRunner()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_cli_remote_check_reports_missing_profile_as_not_ready() -> None:
    result = runner.invoke(
        app,
        ["remote-check", "--execution-mode", "ssh_slurm_trusted"],
        env={"GENEAGENT_HPC_HOST": "", "GENEAGENT_HPC_USER": ""},
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["execution_mode"] == "ssh_slurm_trusted"
    assert payload["safe_for_submit"] is False
    assert "missing_hpc_host" in payload["messages"]


def test_cli_remote_check_shell_mode_reports_missing_profile_as_not_ready() -> None:
    result = runner.invoke(
        app,
        ["remote-check", "--execution-mode", "ssh_shell_trusted"],
        env={"GENEAGENT_HPC_HOST": "", "GENEAGENT_HPC_USER": ""},
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["execution_mode"] == "ssh_shell_trusted"
    assert payload["scheduler"] == "shell"
    assert payload["safe_for_submit"] is False
    assert "missing_hpc_host" in payload["messages"]


def test_cli_remote_check_uses_request_profile_name() -> None:
    result = runner.invoke(
        app,
        ["remote-check", "--execution-mode", "ssh_slurm_trusted", "--remote-profile-name", "ops"],
        env={"GENEAGENT_HPC_HOST": "", "GENEAGENT_HPC_USER": ""},
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["profile_name"] == "ops"
    assert payload["execution_mode"] == "ssh_slurm_trusted"


def test_cli_remote_session_open_prints_control_master_command(tmp_path) -> None:
    control_path = tmp_path / "server.sock"
    result = runner.invoke(
        app,
        ["remote-session-open", "--print-command"],
        env={
            "GENEAGENT_HPC_HOST": "server.example.org",
            "GENEAGENT_HPC_USER": "alice",
            "GENEAGENT_HPC_SSH_AUTH_MODE": "control_master",
            "GENEAGENT_HPC_SSH_CONTROL_PATH": str(control_path),
            "GENEAGENT_HPC_SSH_CONTROL_PERSIST": "2h",
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "open"
    assert payload["auth_mode"] == "control_master"
    assert payload["control_path"] == str(control_path)
    assert "ControlMaster=yes" in payload["command_text"]
    assert "ControlPersist=2h" in payload["command_text"]
    assert "BatchMode=yes" not in payload["command_text"]
    assert "password" not in payload["command_text"].lower()


def test_cli_remote_session_smoke_prints_password_session_flow(tmp_path) -> None:
    control_path = tmp_path / "server.sock"
    result = runner.invoke(
        app,
        [
            "remote-session-smoke",
            "--print-command",
            "--task-id",
            "task-smoke-001",
            "--run-id",
            "run-smoke-001",
        ],
        env={
            "GENEAGENT_HPC_HOST": "server.example.org",
            "GENEAGENT_HPC_USER": "alice",
            "GENEAGENT_HPC_SSH_AUTH_MODE": "control_master",
            "GENEAGENT_HPC_SSH_CONTROL_PATH": str(control_path),
            "GENEAGENT_HPC_SSH_CONTROL_PERSIST": "2h",
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "remote-session-smoke"
    assert payload["auth_mode"] == "control_master"
    assert payload["control_path"] == str(control_path)
    assert "ControlMaster=yes" in payload["open_command_text"]
    assert "BatchMode=yes" not in payload["open_command_text"]
    assert "remote-check --execution-mode ssh_shell_trusted" in payload["next_commands"][0]
    assert "remote-smoke --task-id task-smoke-001 --run-id run-smoke-001" in payload["next_commands"][1]
    assert "password" not in payload["open_command_text"].lower()
    assert "password" not in json.dumps(payload).lower()


def test_cli_remote_session_smoke_missing_profile_fails_without_submit() -> None:
    result = runner.invoke(
        app,
        ["remote-session-smoke", "--no-open-session"],
        env={
            "GENEAGENT_HPC_HOST": "",
            "GENEAGENT_HPC_USER": "",
            "GENEAGENT_HPC_SSH_AUTH_MODE": "control_master",
        },
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["action"] == "remote-session-smoke"
    assert payload["session_ready"] is False
    assert payload["submitted"] is False
    assert "remote_ssh_target_not_configured" in payload["messages"]


def test_cli_remote_session_doctor_reports_ready_local_configuration(tmp_path) -> None:
    control_path = tmp_path / "server.sock"
    result = runner.invoke(
        app,
        ["remote-session-doctor", "--skip-ssh-probe"],
        env={
            "GENEAGENT_EXECUTION_MODE": "ssh_shell_trusted",
            "GENEAGENT_SCHEDULER_REAL_EXECUTION_ENABLED": "true",
            "GENEAGENT_HPC_HOST": "server.example.org",
            "GENEAGENT_HPC_USER": "alice",
            "GENEAGENT_HPC_WORK_ROOT": "/data2/alice/geneagent_runs",
            "GENEAGENT_HPC_SSH_AUTH_MODE": "control_master",
            "GENEAGENT_HPC_SSH_CONTROL_PATH": str(control_path),
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "remote-session-doctor"
    assert payload["ready_for_control_session"] is True
    assert payload["ready_for_real_smoke"] is True
    assert payload["checks"]["execution_mode_ssh_shell_trusted"] is True
    assert payload["checks"]["real_execution_enabled"] is True
    assert payload["checks"]["control_dir_writable"] is True
    assert payload["control_dir_check"]["ok"] is True
    assert payload["recommended_next_command"].startswith("remote-session-smoke --open-session")


def test_cli_remote_session_doctor_blocks_missing_control_master_profile() -> None:
    result = runner.invoke(
        app,
        ["remote-session-doctor", "--skip-ssh-probe"],
        env={
            "GENEAGENT_EXECUTION_MODE": "local_preview",
            "GENEAGENT_SCHEDULER_REAL_EXECUTION_ENABLED": "false",
            "GENEAGENT_HPC_HOST": "",
            "GENEAGENT_HPC_USER": "",
            "GENEAGENT_HPC_SSH_AUTH_MODE": "batch",
        },
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["action"] == "remote-session-doctor"
    assert payload["ready_for_control_session"] is False
    assert payload["ready_for_real_smoke"] is False
    assert payload["control_dir_check"]["ok"] in {True, False}
    assert "execution_mode_not_ssh_shell_trusted" in payload["messages"]
    assert "ssh_auth_mode_not_control_master_or_password_env" in payload["messages"]
    assert "remote_ssh_target_not_configured" in payload["messages"]
    assert any("GENEAGENT_HPC_SSH_AUTH_MODE=control_master" in item for item in payload["remediation"])


def test_cli_remote_session_doctor_supports_password_env_without_leaking_secret() -> None:
    result = runner.invoke(
        app,
        ["remote-session-doctor", "--skip-ssh-probe"],
        env={
            "GENEAGENT_EXECUTION_MODE": "ssh_shell_trusted",
            "GENEAGENT_SCHEDULER_REAL_EXECUTION_ENABLED": "true",
            "GENEAGENT_HPC_HOST": "server.example.org",
            "GENEAGENT_HPC_USER": "alice",
            "GENEAGENT_HPC_WORK_ROOT": "/data2/alice/geneagent_runs",
            "GENEAGENT_HPC_SSH_AUTH_MODE": "password_env",
            "GENEAGENT_HPC_SSH_PASSWORD": "top-secret",
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action"] == "remote-session-doctor"
    assert payload["auth_mode"] == "password_env"
    assert payload["ready_for_auth"] is True
    assert payload["ready_for_real_smoke"] is True
    assert payload["checks"]["ssh_password_configured"] is True
    assert payload["recommended_next_command"].startswith("remote-smoke")
    assert "top-secret" not in result.stdout


def test_cli_remote_password_set_writes_only_local_env_and_redacts_stdout(tmp_path) -> None:
    env_file = tmp_path / ".env"
    result = runner.invoke(
        app,
        ["remote-password-set", "--env-file", str(env_file)],
        input="top-secret\n",
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["action"] == "remote-password-set"
    assert payload["auth_mode"] == "password_env"
    assert payload["password_configured"] is True
    assert "top-secret" not in result.stdout
    contents = env_file.read_text(encoding="utf-8")
    assert "GENEAGENT_HPC_SSH_AUTH_MODE=password_env" in contents
    assert "GENEAGENT_HPC_SSH_PASSWORD=top-secret" in contents


def test_cli_remote_smoke_blocks_without_ready_remote_profile() -> None:
    result = runner.invoke(
        app,
        ["remote-smoke"],
        env={"GENEAGENT_HPC_HOST": "", "GENEAGENT_HPC_USER": ""},
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["submitted"] is False
    assert payload["remote_check"]["safe_for_submit"] is False
    assert "missing_hpc_host" in payload["messages"]


def test_cli_submit_preview_manual_sbase_prints_submit_card(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            "submit-preview",
            "--execution-mode",
            "manual_sbase",
            "--task-id",
            "task-cli-sbase-001",
            "--run-id",
            "run-cli-sbase-001",
            "--working-directory",
            "/cluster/work/sheep",
            "--request-text",
            "Submit preview for sheep PCA on VCF panel",
            "--dry-run-completed",
        ],
        env={
            "GENEAGENT_EXECUTION_MODE": "local_preview",
            "GENEAGENT_LOCAL_STATE_ROOT": str(tmp_path / ".geneagent"),
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["execution_mode"] == "manual_sbase"
    assert payload["manual_submit_card"] is not None
    assert "sbatch" in payload["manual_submit_card"]["sbatch_wrap_command"]


def test_cli_submit_preview_shell_mode_uses_remote_work_root(tmp_path) -> None:
    result = runner.invoke(
        app,
        [
            "submit-preview",
            "--execution-mode",
            "ssh_shell_trusted",
            "--task-id",
            "task-cli-shell-001",
            "--run-id",
            "run-cli-shell-001",
            "--working-directory",
            "D:/local/project",
            "--request-text",
            "Submit preview for cattle QC on VCF panel",
            "--dry-run-completed",
        ],
        env={
            "GENEAGENT_LOCAL_STATE_ROOT": str(tmp_path / ".geneagent"),
            "GENEAGENT_HPC_WORK_ROOT": "/data2/alice/geneagent_runs",
        },
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["execution_mode"] == "ssh_shell_trusted"
    assert payload["job_handle"]["scheduler"] == "shell"
    assert payload["working_directory"] == "/data2/alice/geneagent_runs/task-cli-shell-001/run-cli-shell-001"
    assert payload["scheduler_script_path"].endswith("/run.sh")
    assert payload["run_state"]["scheduler"] == "shell"


def test_cli_watch_run_missing_state_returns_clear_error() -> None:
    result = runner.invoke(app, ["watch-run", "--task-id", "missing-task", "--run-id", "missing-run"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"] == "run_state_not_found"
