from functools import lru_cache
from typing import Annotated, Final, Literal
from urllib.parse import quote

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Output size of the embedding model. This is baked into the database schema
# (Vector column), so it is a constant, not an env-configurable setting.
# Measured against Ollama's all-minilm: 384.
EMBEDDING_DIM: Final = 384


class Settings(BaseSettings):
    """Process-wide configuration. Secrets come from the environment only."""

    model_config = SettingsConfigDict(env_prefix="SCAI_", env_file=".env", extra="ignore")

    env: Literal["local", "test", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    db_host: str = "127.0.0.1"
    db_port: Annotated[int, Field(ge=1, le=65535)] = 5432
    db_name: str = "scai"
    db_user: str = "scai"
    # No default: the password only ever comes from the environment.
    db_password: SecretStr | None = None
    embedding_model: str = "all-minilm"

    @property
    def database_url(self) -> SecretStr:
        """SQLAlchemy URL (psycopg 3 driver), wrapped so it never prints."""
        if self.db_password is None:
            raise ValueError("SCAI_DB_PASSWORD is not set")
        password = quote(self.db_password.get_secret_value(), safe="")
        url = (
            f"postgresql+psycopg://{quote(self.db_user, safe='')}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return SecretStr(url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
