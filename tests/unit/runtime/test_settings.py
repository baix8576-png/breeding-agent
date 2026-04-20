from runtime.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "GeneAgent"
    assert settings.scheduler_type.value == "slurm"
    assert settings.dry_run_default is True
    assert settings.scheduler_real_execution_enabled is False
    assert settings.scheduler_retry_max_attempts == 3
    assert settings.scheduler_retry_backoff_seconds == [2, 5, 10]
    assert settings.scheduler_command_timeout_seconds == 60
    assert settings.knowledge_external_fallback_enabled is True
    assert settings.knowledge_external_fallback_policy == "knowledge_only"


def test_settings_supports_pbs_scheduler_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GENEAGENT_SCHEDULER_TYPE", "pbs")

    settings = Settings()

    assert settings.scheduler_type.value == "pbs"


def test_settings_supports_external_fallback_policy_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GENEAGENT_KNOWLEDGE_EXTERNAL_FALLBACK_ENABLED", "false")
    monkeypatch.setenv("GENEAGENT_KNOWLEDGE_EXTERNAL_FALLBACK_POLICY", "diagnostic_only")

    settings = Settings()

    assert settings.knowledge_external_fallback_enabled is False
    assert settings.knowledge_external_fallback_policy == "diagnostic_only"
