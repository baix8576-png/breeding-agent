from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import create_app
from runtime.settings import get_settings


def test_remote_check_route_without_host_is_safe_false(monkeypatch) -> None:
    monkeypatch.delenv("GENEAGENT_HPC_HOST", raising=False)
    monkeypatch.delenv("GENEAGENT_HPC_USER", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post("/tasks/remote-check", json={"execution_mode": "ssh_slurm_trusted"})

        assert response.status_code == 200
        remote_check = response.json()["remote_check"]
        assert remote_check["execution_mode"] == "ssh_slurm_trusted"
        assert remote_check["safe_for_submit"] is False
        assert "missing_hpc_host" in remote_check["messages"]
    finally:
        get_settings.cache_clear()


def test_remote_check_shell_mode_without_host_is_safe_false(monkeypatch) -> None:
    monkeypatch.delenv("GENEAGENT_HPC_HOST", raising=False)
    monkeypatch.delenv("GENEAGENT_HPC_USER", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post("/tasks/remote-check", json={"execution_mode": "ssh_shell_trusted"})

        assert response.status_code == 200
        remote_check = response.json()["remote_check"]
        assert remote_check["execution_mode"] == "ssh_shell_trusted"
        assert remote_check["scheduler"] == "shell"
        assert remote_check["safe_for_submit"] is False
        assert "missing_hpc_host" in remote_check["messages"]
    finally:
        get_settings.cache_clear()


def test_remote_check_uses_request_profile_name_for_ssh_mode(monkeypatch) -> None:
    monkeypatch.delenv("GENEAGENT_HPC_HOST", raising=False)
    monkeypatch.delenv("GENEAGENT_HPC_USER", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post(
            "/tasks/remote-check",
            json={
                "execution_mode": "ssh_slurm_trusted",
                "remote_profile_name": "ops",
            },
        )

        assert response.status_code == 200
        remote_check = response.json()["remote_check"]
        assert remote_check["profile_name"] == "ops"
        assert remote_check["execution_mode"] == "ssh_slurm_trusted"
    finally:
        get_settings.cache_clear()


def test_v2_remote_check_route_is_exposed(monkeypatch) -> None:
    monkeypatch.delenv("GENEAGENT_HPC_HOST", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post("/v2/tasks/remote-check", json={})

        assert response.status_code == 200
        assert response.headers["X-GeneAgent-API-Version"] == "v2"
        assert "remote_check" in response.json()
    finally:
        get_settings.cache_clear()


def test_v2_remote_check_route_accepts_shell_mode(monkeypatch) -> None:
    monkeypatch.delenv("GENEAGENT_HPC_HOST", raising=False)
    monkeypatch.delenv("GENEAGENT_HPC_USER", raising=False)
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post("/v2/tasks/remote-check", json={"execution_mode": "ssh_shell_trusted"})

        assert response.status_code == 200
        assert response.headers["X-GeneAgent-API-Version"] == "v2"
        assert response.json()["remote_check"]["execution_mode"] == "ssh_shell_trusted"
        assert response.json()["remote_check"]["scheduler"] == "shell"
    finally:
        get_settings.cache_clear()


def test_submit_preview_manual_sbase_returns_submit_card(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GENEAGENT_LOCAL_STATE_ROOT", str(tmp_path / ".geneagent"))
    get_settings.cache_clear()
    client = TestClient(create_app())
    try:
        response = client.post(
            "/tasks/submit-preview",
            json={
                "request_text": "Submit preview for sheep PCA on VCF panel",
                "execution_mode": "manual_sbase",
                "dry_run_completed": True,
                "identity": {
                    "task_id": "task-api-sbase-001",
                    "run_id": "run-api-sbase-001",
                    "working_directory": "/cluster/work/sheep",
                },
            },
        )

        assert response.status_code == 200
        submission = response.json()["submission"]
        assert submission["execution_mode"] == "manual_sbase"
        assert submission["manual_submit_card"] is not None
        assert submission["manual_submit_card"]["scheduler"] == "slurm"
        assert "sbatch" in submission["manual_submit_card"]["sbatch_wrap_command"]
        assert submission["run_state_path"] is not None
    finally:
        get_settings.cache_clear()


def test_submit_preview_shell_mode_uses_remote_shell_backend_from_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GENEAGENT_LOCAL_STATE_ROOT", str(tmp_path / ".geneagent"))
    monkeypatch.setenv("GENEAGENT_HPC_WORK_ROOT", "/data2/alice/geneagent_runs")
    get_settings.cache_clear()
    client = TestClient(create_app())
    try:
        response = client.post(
            "/tasks/submit-preview",
            json={
                "request_text": "Submit preview for cattle QC on VCF panel",
                "execution_mode": "ssh_shell_trusted",
                "dry_run_completed": True,
                "identity": {
                    "task_id": "task-api-shell-001",
                    "run_id": "run-api-shell-001",
                    "working_directory": "D:/local/project",
                },
            },
        )

        assert response.status_code == 200
        submission = response.json()["submission"]
        assert submission["execution_mode"] == "ssh_shell_trusted"
        assert submission["job_handle"]["scheduler"] == "shell"
        assert submission["working_directory"] == "/data2/alice/geneagent_runs/task-api-shell-001/run-api-shell-001"
        assert submission["scheduler_script_path"].endswith("/run.sh")
        assert submission["remote_check_summary"]["scheduler"] == "shell"
        assert submission["run_state"]["scheduler"] == "shell"
    finally:
        get_settings.cache_clear()
