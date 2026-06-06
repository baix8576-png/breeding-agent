from runtime.settings import Settings
from runtime.bootstrap import create_application_context
from scheduler.ssh_shell import RemoteShellSchedulerAdapter


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "GeneAgent"
    assert settings.scheduler_type.value == "slurm"
    assert settings.execution_mode.value == "local_preview"
    assert settings.remote_profile_name == "default"
    assert settings.dry_run_default is True
    assert settings.scheduler_real_execution_enabled is False
    assert settings.scheduler_idempotent_submit_enabled is True
    assert settings.scheduler_retry_max_attempts == 3
    assert settings.scheduler_retry_backoff_seconds == [2, 5, 10]
    assert settings.scheduler_command_timeout_seconds == 60
    assert settings.scheduler_quota_cpu_hours_limit == 1024.0
    assert settings.scheduler_quota_memory_gb_limit == 512
    assert settings.scheduler_quota_max_concurrent_jobs == 64
    assert settings.scheduler_current_active_jobs == 0
    assert settings.hpc_host is None
    assert settings.hpc_port == 22
    assert settings.hpc_work_root == "/cluster/work/geneagent"
    assert settings.remote_allowed_write_roots == []
    assert settings.remote_shell_cpu_cap == 32
    assert settings.remote_shell_memory_gb_cap == 256
    assert settings.remote_shell_walltime_cap == "24:00:00"
    assert settings.remote_shell_max_concurrent_runs == 2
    assert settings.remote_shell_process_limits_enabled is True
    assert settings.hpc_connect_timeout_seconds == 15
    assert settings.remote_auto_continue_enabled is True
    assert settings.remote_auto_repair_level.value == "trusted"
    assert settings.local_state_root == ".geneagent"
    assert settings.outbound_policy_enforced is True
    assert settings.knowledge_external_fallback_enabled is True
    assert settings.knowledge_external_fallback_policy == "tiered"
    assert settings.knowledge_external_fallback_default_sensitivity == "low"
    assert settings.knowledge_external_fallback_domain_sensitivity_limits == {
        "bioinformatics": "low",
        "knowledge": "medium",
        "system": "low",
    }
    assert settings.api_current_version == "v2"
    assert settings.api_v1_prefix == "/tasks"
    assert settings.api_v2_prefix == "/v2/tasks"
    assert settings.api_v1_deprecation_started_at == "2026-05-09"
    assert settings.api_v1_sunset_date == "2026-11-09"
    assert settings.api_compatibility_window_days == 180
    assert settings.api_version_policy_path == "/v2/version-policy"


def test_settings_supports_pbs_scheduler_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GENEAGENT_SCHEDULER_TYPE", "pbs")

    settings = Settings()

    assert settings.scheduler_type.value == "pbs"


def test_settings_supports_ssh_shell_trusted_execution_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GENEAGENT_EXECUTION_MODE", "ssh_shell_trusted")
    monkeypatch.setenv("GENEAGENT_HPC_WORK_ROOT", "/data2/alice/geneagent_runs")
    monkeypatch.setenv("GENEAGENT_HPC_SSH_AUTH_MODE", "control_master")
    monkeypatch.setenv("GENEAGENT_HPC_SSH_CONTROL_PATH", ".geneagent/ssh_control/server.sock")
    monkeypatch.setenv("GENEAGENT_HPC_SSH_CONTROL_PERSIST", "2h")
    monkeypatch.setenv("GENEAGENT_REMOTE_ALLOWED_WRITE_ROOTS", '["/data2/alice"]')
    monkeypatch.setenv("GENEAGENT_REMOTE_SHELL_CPU_CAP", "2")
    monkeypatch.setenv("GENEAGENT_REMOTE_SHELL_MEMORY_GB_CAP", "8")
    monkeypatch.setenv("GENEAGENT_REMOTE_SHELL_WALLTIME_CAP", "01:00:00")
    monkeypatch.setenv("GENEAGENT_REMOTE_SHELL_MAX_CONCURRENT_RUNS", "1")

    settings = Settings()

    assert settings.execution_mode.value == "ssh_shell_trusted"
    assert settings.remote_allowed_write_roots == ["/data2/alice"]
    assert settings.remote_shell_cpu_cap == 2
    assert settings.remote_shell_memory_gb_cap == 8
    assert settings.remote_shell_walltime_cap == "01:00:00"
    assert settings.remote_shell_max_concurrent_runs == 1
    profile = settings.remote_execution_profile()
    assert profile.work_root == "/data2/alice/geneagent_runs"
    assert profile.allowed_write_roots == ["/data2/alice"]
    assert profile.ssh_auth_mode.value == "control_master"
    assert profile.ssh_control_path == ".geneagent/ssh_control/server.sock"
    assert profile.ssh_control_persist == "2h"


def test_settings_supports_password_env_auth_without_serializing_secret(monkeypatch) -> None:
    monkeypatch.setenv("GENEAGENT_HPC_SSH_AUTH_MODE", "password_env")
    monkeypatch.setenv("GENEAGENT_HPC_SSH_PASSWORD", "top-secret")

    settings = Settings()
    profile = settings.remote_execution_profile()

    assert profile.ssh_auth_mode.value == "password_env"
    assert profile.ssh_password_configured is True
    assert profile.ssh_password is not None
    assert profile.ssh_password.get_secret_value() == "top-secret"
    assert "ssh_password" not in profile.model_dump()


def test_bootstrap_builds_remote_shell_scheduler_for_shell_mode(tmp_path) -> None:
    settings = Settings(
        execution_mode="ssh_shell_trusted",
        hpc_host="server.example.org",
        hpc_user="alice",
        hpc_work_root="/data2/alice/geneagent_runs",
        local_state_root=str(tmp_path / ".geneagent"),
    )

    context = create_application_context(settings=settings)

    assert isinstance(context.scheduler, RemoteShellSchedulerAdapter)
    assert context.scheduler.kind.value == "shell"
    assert context.scheduler._remote_cpu_cap == 32
    assert context.scheduler._remote_memory_gb_cap == 256
    assert context.scheduler._remote_walltime_cap == "24:00:00"
    assert context.scheduler._remote_max_concurrent_runs == 2


def test_settings_supports_external_fallback_policy_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GENEAGENT_KNOWLEDGE_EXTERNAL_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("GENEAGENT_KNOWLEDGE_EXTERNAL_FALLBACK_POLICY", "diagnostic_only")
    monkeypatch.setenv("GENEAGENT_KNOWLEDGE_EXTERNAL_FALLBACK_DEFAULT_SENSITIVITY", "medium")
    monkeypatch.setenv(
        "GENEAGENT_KNOWLEDGE_EXTERNAL_FALLBACK_DOMAIN_SENSITIVITY_LIMITS",
        '{"bioinformatics":"low","knowledge":"high","system":"medium"}',
    )
    monkeypatch.setenv("GENEAGENT_SCHEDULER_QUOTA_CPU_HOURS_LIMIT", "256")
    monkeypatch.setenv("GENEAGENT_SCHEDULER_QUOTA_MEMORY_GB_LIMIT", "128")
    monkeypatch.setenv("GENEAGENT_SCHEDULER_QUOTA_MAX_CONCURRENT_JOBS", "16")
    monkeypatch.setenv("GENEAGENT_SCHEDULER_CURRENT_ACTIVE_JOBS", "3")
    monkeypatch.setenv("GENEAGENT_OUTBOUND_POLICY_ENFORCED", "false")
    monkeypatch.setenv("GENEAGENT_EXECUTION_MODE", "manual_sbase")
    monkeypatch.setenv("GENEAGENT_REMOTE_PROFILE_NAME", "ops")
    monkeypatch.setenv("GENEAGENT_HPC_HOST", "hpc.example.org")
    monkeypatch.setenv("GENEAGENT_HPC_USER", "alice")
    monkeypatch.setenv("GENEAGENT_HPC_PORT", "2222")
    monkeypatch.setenv("GENEAGENT_HPC_WORK_ROOT", "/cluster/work/alice/geneagent")
    monkeypatch.setenv("GENEAGENT_HPC_DEFAULT_PARTITION", "x86-shared")
    monkeypatch.setenv("GENEAGENT_HPC_TOOL_PATHS", '{"plink":"/opt/plink"}')
    monkeypatch.setenv("GENEAGENT_HPC_CONNECT_TIMEOUT_SECONDS", "9")
    monkeypatch.setenv("GENEAGENT_HPC_SSH_AUTH_MODE", "control_master")
    monkeypatch.setenv("GENEAGENT_HPC_SSH_CONTROL_PATH", ".geneagent/ssh_control/ops.sock")
    monkeypatch.setenv("GENEAGENT_REMOTE_AUTO_CONTINUE_ENABLED", "false")
    monkeypatch.setenv("GENEAGENT_REMOTE_AUTO_REPAIR_LEVEL", "low_risk")
    monkeypatch.setenv("GENEAGENT_LOCAL_STATE_ROOT", ".geneagent-test")
    monkeypatch.setenv("GENEAGENT_API_V1_SUNSET_DATE", "2026-12-31")
    monkeypatch.setenv("GENEAGENT_API_COMPATIBILITY_WINDOW_DAYS", "365")

    settings = Settings()

    assert settings.knowledge_external_fallback_enabled is False
    assert settings.knowledge_external_fallback_policy == "diagnostic_only"
    assert settings.knowledge_external_fallback_default_sensitivity == "medium"
    assert settings.knowledge_external_fallback_domain_sensitivity_limits == {
        "bioinformatics": "low",
        "knowledge": "high",
        "system": "medium",
    }
    assert settings.scheduler_quota_cpu_hours_limit == 256.0
    assert settings.scheduler_quota_memory_gb_limit == 128
    assert settings.scheduler_quota_max_concurrent_jobs == 16
    assert settings.scheduler_current_active_jobs == 3
    assert settings.outbound_policy_enforced is False
    assert settings.api_v1_sunset_date == "2026-12-31"
    assert settings.api_compatibility_window_days == 365
    assert settings.execution_mode.value == "manual_sbase"
    assert settings.remote_profile_name == "ops"
    assert settings.hpc_host == "hpc.example.org"
    assert settings.hpc_user == "alice"
    assert settings.hpc_port == 2222
    assert settings.hpc_work_root == "/cluster/work/alice/geneagent"
    assert settings.hpc_default_partition == "x86-shared"
    assert settings.hpc_tool_paths == {"plink": "/opt/plink"}
    assert settings.hpc_connect_timeout_seconds == 9
    assert settings.remote_auto_continue_enabled is False
    assert settings.remote_auto_repair_level.value == "low_risk"
    assert settings.local_state_root == ".geneagent-test"
    profile = settings.remote_execution_profile()
    assert profile.profile_name == "ops"
    assert profile.ssh_target == "alice@hpc.example.org"
    assert profile.connect_timeout_seconds == 9
    assert profile.ssh_auth_mode.value == "control_master"
    assert profile.ssh_control_path == ".geneagent/ssh_control/ops.sock"
