"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from contracts.common import SchedulerKind


class Settings(BaseSettings):
    """Centralized runtime settings for GeneAgent V1."""

    app_name: str = "GeneAgent"
    app_env: str = "dev"
    model_provider: str = "openai"
    model_name: str = "gpt-5.4"
    scheduler_type: SchedulerKind = SchedulerKind.SLURM
    conda_env_name: str = "geneagent-base"
    work_root: str = "/cluster/work/geneagent"
    log_root: str = "/cluster/work/geneagent/logs"
    knowledge_base_root: str = "/cluster/work/geneagent/knowledge"
    knowledge_external_fallback_enabled: bool = True
    knowledge_external_fallback_policy: str = "knowledge_only"
    max_cpu: int = 64
    max_mem_gb: int = 256
    dry_run_default: bool = True
    scheduler_real_execution_enabled: bool = False
    scheduler_retry_max_attempts: int = 3
    scheduler_retry_backoff_seconds: list[int] = Field(default_factory=lambda: [2, 5, 10])
    scheduler_command_timeout_seconds: int = 60
    allow_cloud_fields: list[str] = Field(
        default_factory=lambda: [
            "prompt",
            "sanitized_error_log",
            "tool_summary",
            "software_version",
            "parameter_schema",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GENEAGENT_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object for API and CLI entry points."""

    return Settings()
