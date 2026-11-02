from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from aithena.config.settings import Model
from aithena.llm.client import ClaudeClient, ClaudeResponseError
from aithena.models.schemas import LicenseInfo
from tests.fakes import FakeClient, as_sdk

EXPECTED = LicenseInfo(copyright_holder="Ada", license_name="MIT", license_type="permissive")


def call(llm: ClaudeClient, path: Path) -> LicenseInfo:
    return llm.parse(
        model=Model.HAIKU_5_5,
        path=path,
        system="sys",
        tag="header",
        text="# MIT License",
        schema=LicenseInfo,
    )


def test_returns_parsed_output_and_uses_requested_model(make_client, tmp_path: Path) -> None:
    fake = make_client(lambda _schema, _text: EXPECTED)
    llm = ClaudeClient(as_sdk(fake))

    result = call(llm, tmp_path / "a.py")

    assert result == EXPECTED
    assert fake.beta.messages.calls == [(Model.HAIKU_5_5, LicenseInfo)]


def test_usage_counts_calls_and_tokens(make_client, tmp_path: Path) -> None:
    llm = ClaudeClient(as_sdk(make_client(lambda _schema, _text: EXPECTED)))

    call(llm, tmp_path / "a.py")

    assert (llm.usage.calls, llm.usage.input_tokens, llm.usage.output_tokens) == (1, 100, 20)


def test_refusal_raises_specific_error(tmp_path: Path) -> None:
    class RefusingMessages:
        def parse(self, **_: Any) -> SimpleNamespace:
            usage = SimpleNamespace(input_tokens=5, output_tokens=0)
            return SimpleNamespace(
                stop_reason="refusal", stop_details="policy", parsed_output=None, usage=usage
            )

    fake = FakeClient(lambda _schema, _text: None)
    fake.beta.messages = RefusingMessages()  # type: ignore[assignment]

    with pytest.raises(ClaudeResponseError, match="declined"):
        call(ClaudeClient(as_sdk(fake)), tmp_path / "a.py")


def test_missing_structured_output_raises(make_client, tmp_path: Path) -> None:
    llm = ClaudeClient(as_sdk(make_client(lambda _schema, _text: None)))

    with pytest.raises(ClaudeResponseError, match="No structured output"):
        call(llm, tmp_path / "a.py")
