from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from aithena.config.settings import Model
from aithena.llm.client import ClaudeResponseError, parse_source
from aithena.models.schemas import LicenseInfo
from tests.fakes import FakeClient


def _call(client: Any, path: Path) -> LicenseInfo:
    return parse_source(
        client,
        model=Model.HAIKU_5_5,
        path=path,
        system="sys",
        tag="header",
        text="# MIT License",
        schema=LicenseInfo,
    )


def test_returns_parsed_output_and_uses_requested_model(make_client, tmp_path: Path) -> None:
    expected = LicenseInfo(copyright_holder="Ada", license_name="MIT", license_type="permissive")
    client = make_client(lambda _schema, _text: expected)

    result = _call(client, tmp_path / "a.py")

    assert result == expected
    assert client.beta.messages.calls == [(Model.HAIKU_5_5, LicenseInfo)]


def test_refusal_raises_specific_error(tmp_path: Path) -> None:
    class RefusingMessages:
        def parse(self, **_: Any) -> SimpleNamespace:
            return SimpleNamespace(stop_reason="refusal", stop_details="policy", parsed_output=None)

    client = FakeClient(lambda _schema, _text: None)
    client.beta.messages = RefusingMessages()  # type: ignore[assignment]

    with pytest.raises(ClaudeResponseError, match="declined"):
        _call(client, tmp_path / "a.py")
