"""GeneAgent V2 application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from contracts.common import AutoRepairLevel, ExecutionMode, SchedulerKind, SshAuthMode, TaskDomain
from contracts.remote_execution import RemoteExecutionProfile


def _settings_env_file() -> str | None:
    override = os.environ.get("GENEAGENT_ENV_FILE")
    if override is None:
        return ".env"
    normalized = override.strip().lower()
    if normalized in {"", "0", "false", "none", "off"}:
        return None
    return override


class Settings(BaseSettings):
    """Centralized runtime settings for GeneAgent V2."""

    app_name: str = "GeneAgent"
    app_env: str = "dev"
    model_provider: str = "openai"
    model_name: str = "gpt-5.4"
    scheduler_type: SchedulerKind = SchedulerKind.SLURM
    execution_mode: ExecutionMode = ExecutionMode.LOCAL_PREVIEW
    remote_profile_name: str = "default"
    conda_env_name: str = "geneagent-base"
    work_root: str = "/cluster/work/geneagent"
    log_root: str = "/cluster/work/geneagent/logs"
    knowledge_base_root: str = "/cluster/work/geneagent/knowledge"
    knowledge_external_fallback_enabled: bool = True
    knowledge_external_fallback_policy: str = "tiered"
    knowledge_external_fallback_default_sensitivity: str = "low"
    knowledge_external_fallback_domain_sensitivity_limits: dict[str, str] = Field(
        default_factory=lambda: {
            TaskDomain.BIOINFORMATICS.value: "low",
            TaskDomain.KNOWLEDGE.value: "medium",
            TaskDomain.SYSTEM.value: "low",
        }
    )
    max_cpu: int = 64
    max_mem_gb: int = 256
    dry_run_default: bool = True
    scheduler_real_execution_enabled: bool = False
    scheduler_idempotent_submit_enabled: bool = True
    scheduler_retry_max_attempts: int = 3
    scheduler_retry_backoff_seconds: list[int] = Field(default_factory=lambda: [2, 5, 10])
    scheduler_command_timeout_seconds: int = 60
    scheduler_quota_cpu_hours_limit: float = 1024.0
    scheduler_quota_memory_gb_limit: int = 512
    scheduler_quota_max_concurrent_jobs: int = 64
    scheduler_current_active_jobs: int = 0
    hpc_host: str | None = None
    hpc_user: str | None = None
    hpc_port: int = 22
    hpc_work_root: str = "/cluster/work/geneagent"
    remote_allowed_write_roots: list[str] = Field(default_factory=list)
    remote_shell_cpu_cap: int = 32
    remote_shell_memory_gb_cap: int = 256
    remote_shell_walltime_cap: str = "24:00:00"
    remote_shell_max_concurrent_runs: int = 2
    remote_shell_process_limits_enabled: bool = True
    hpc_default_partition: str | None = None
    hpc_tool_paths: dict[str, str] = Field(default_factory=dict)
    hpc_ssh_binary: str = "ssh"
    hpc_ssh_auth_mode: SshAuthMode = SshAuthMode.BATCH
    hpc_ssh_control_path: str | None = None
    hpc_ssh_control_persist: str = "4h"
    hpc_ssh_password: SecretStr | None = Field(default=None, repr=False)
    hpc_strict_host_key_checking: str = "accept-new"
    hpc_connect_timeout_seconds: int = 15
    local_state_root: str = ".geneagent"
    remote_auto_continue_enabled: bool = True
    remote_auto_repair_level: AutoRepairLevel = AutoRepairLevel.TRUSTED
    outbound_policy_enforced: bool = True
    allow_cloud_fields: list[str] = Field(
        default_factory=lambda: [
            "prompt",
            "sanitized_error_log",
            "tool_summary",
            "software_version",
            "parameter_schema",
        ]
    )
    api_current_version: str = "v2"
    api_v1_prefix: str = "/tasks"
    api_v2_prefix: str = "/v2/tasks"
    api_v1_deprecation_started_at: str = "2026-05-09"
    api_v1_sunset_date: str = "2026-11-09"
    api_compatibility_window_days: int = 180
    api_version_policy_path: str = "/v2/version-policy"

    model_config = SettingsConfigDict(
        env_file=_settings_env_file(),
        env_prefix="GENEAGENT_",
        extra="ignore",
    )

    def remote_execution_profile(self, profile_name: str | None = None) -> RemoteExecutionProfile:
        """Build the configured remote profile without exposing credentials."""

        return RemoteExecutionProfile(
            profile_name=profile_name or self.remote_profile_name,
            host=self.hpc_host,
            user=self.hpc_user,
            port=self.hpc_port,
            work_root=self.hpc_work_root,
            allowed_write_roots=self.remote_allowed_write_roots,
            default_partition=self.hpc_default_partition,
            tool_paths=self.hpc_tool_paths,
            ssh_binary=self.hpc_ssh_binary,
            ssh_auth_mode=self.hpc_ssh_auth_mode,
            ssh_control_path=self.hpc_ssh_control_path or self._default_ssh_control_path(profile_name),
            ssh_control_persist=self.hpc_ssh_control_persist,
            ssh_password=self.hpc_ssh_password,
            strict_host_key_checking=self.hpc_strict_host_key_checking,
            connect_timeout_seconds=self.hpc_connect_timeout_seconds,
        )

    def _default_ssh_control_path(self, profile_name: str | None = None) -> str | None:
        """Return a local control-socket path only when control master mode is enabled."""

        if self.hpc_ssh_auth_mode != SshAuthMode.CONTROL_MASTER:
            return None
        raw_name = profile_name or self.remote_profile_name
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in raw_name)
        return str(Path(self.local_state_root) / "ssh_control" / f"{safe_name}.sock")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for API and CLI entry points."""

    return Settings()
