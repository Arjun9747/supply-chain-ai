from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration. Secrets come from the environment only."""

    model_config = SettingsConfigDict(env_prefix="SCAI_", env_file=".env", extra="ignore")

    env: Literal["local", "test", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
