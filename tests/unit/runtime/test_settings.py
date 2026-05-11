from runtime.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "GeneAgent"
    assert settings.scheduler_type.value == "slurm"
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
