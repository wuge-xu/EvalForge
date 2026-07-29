from typing import Any

import pytest

from evalforge import __main__
from evalforge.core.config import Settings


def test_main_starts_uvicorn_with_application_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        _env_file=None,
        host="127.0.0.1",
        port=8123,
        log_level="WARNING",
    )
    captured: dict[str, Any] = {}

    monkeypatch.setattr(__main__, "get_settings", lambda: settings)

    def fake_run(application: str, **kwargs: Any) -> None:
        captured["application"] = application
        captured.update(kwargs)

    monkeypatch.setattr(__main__.uvicorn, "run", fake_run)

    __main__.main()

    assert captured == {
        "application": "evalforge.main:app",
        "host": "127.0.0.1",
        "port": 8123,
        "log_level": "warning",
        "reload": False,
    }
