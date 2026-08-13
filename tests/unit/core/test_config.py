import pytest
from pydantic import ValidationError

from evalforge.core.config import (
    Environment,
    Settings,
    get_settings,
    reset_settings_cache,
)


def test_default_settings() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "EvalForge"
    assert settings.app_version == "0.1.0"
    assert settings.environment is Environment.DEVELOPMENT
    assert settings.debug is False
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.log_level == "INFO"
    assert settings.is_production is False


def test_settings_can_be_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVALFORGE_ENVIRONMENT", "production")
    monkeypatch.setenv("EVALFORGE_DEBUG", "true")
    monkeypatch.setenv("EVALFORGE_PORT", "8080")
    monkeypatch.setenv("EVALFORGE_LOG_LEVEL", "WARNING")

    settings = Settings(_env_file=None)

    assert settings.environment is Environment.PRODUCTION
    assert settings.debug is True
    assert settings.port == 8080
    assert settings.log_level == "WARNING"
    assert settings.is_production is True


def test_invalid_port_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVALFORGE_PORT", "70000")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_returns_cached_instance() -> None:
    reset_settings_cache()

    first = get_settings()
    second = get_settings()

    assert first is second

    reset_settings_cache()


def test_database_settings_can_be_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "EVALFORGE_DATABASE_URL",
        "postgresql+psycopg://user:password@db:5432/testdb",
    )
    monkeypatch.setenv("EVALFORGE_DATABASE_ECHO", "true")

    settings = Settings(_env_file=None)

    assert settings.database_url == "postgresql+psycopg://user:password@db:5432/testdb"
    assert settings.database_echo is True
