from runtime.settings import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "GeneAgent"
    assert settings.scheduler_type.value == "slurm"
    assert settings.dry_run_default is True
