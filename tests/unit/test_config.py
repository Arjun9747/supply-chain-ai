import pytest
from pydantic import ValidationError

from scai.core.config import Settings, get_settings

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
