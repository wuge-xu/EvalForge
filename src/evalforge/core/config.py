from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="EVALFORGE_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "EvalForge"
    app_version: str = "0.1.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://evalforge:evalforge_dev@127.0.0.1:55432/evalforge"
    database_echo: bool = False

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
