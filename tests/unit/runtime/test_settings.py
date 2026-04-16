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
