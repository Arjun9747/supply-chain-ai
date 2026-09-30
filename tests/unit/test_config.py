import pytest
from pydantic import ValidationError

from scai.core.config import EMBEDDING_DIM, Settings, get_settings

pytestmark = pytest.mark.unit


def test_defaults() -> None:
    assert Settings().env == "local"


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAI_ENV", "prod")
    assert Settings().env == "prod"


def test_invalid_env_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAI_ENV", "yolo")
    with pytest.raises(ValidationError, match="env"):
        Settings()


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()


def test_database_url_requires_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCAI_DB_PASSWORD", raising=False)
    settings = Settings(_env_file=None)
    with pytest.raises(ValueError, match="SCAI_DB_PASSWORD"):
        _ = settings.database_url


def test_database_url_escapes_special_characters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAI_DB_PASSWORD", "p@ss/word:1")
    url = Settings(_env_file=None).database_url.get_secret_value()
    assert url == "postgresql+psycopg://scai:p%40ss%2Fword%3A1@127.0.0.1:5432/scai"


def test_password_never_appears_in_repr_or_str(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAI_DB_PASSWORD", "supersecret")
    settings = Settings(_env_file=None)
    assert "supersecret" not in repr(settings)
    assert "supersecret" not in str(settings.database_url)


def test_invalid_db_port_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAI_DB_PORT", "70000")
    with pytest.raises(ValidationError, match="db_port"):
        Settings(_env_file=None)


def test_embedding_defaults() -> None:
    assert Settings(_env_file=None).embedding_model == "all-minilm"
    assert EMBEDDING_DIM == 384


def test_embedding_model_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAI_EMBEDDING_MODEL", "nomic-embed-text")
    assert Settings(_env_file=None).embedding_model == "nomic-embed-text"
