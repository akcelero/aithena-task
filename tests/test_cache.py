from collections.abc import Callable
from pathlib import Path

import pytest

from aithena.config.settings import Model
from aithena.llm.cache import JsonCache, request_key
from aithena.llm.client import BudgetExceededError, ClaudeClient
from aithena.models.schemas import LicenseInfo
from tests.fakes import FakeClient, Responder, as_sdk

INFO = LicenseInfo(copyright_holder="Ada", license_name="MIT", license_type="permissive")

MakeClient = Callable[[Responder], FakeClient]


def parse(llm: ClaudeClient, text: str) -> LicenseInfo:
    return llm.parse(
        model=Model.HAIKU_5_5,
        path=Path("a.py"),
        system="sys",
        tag="header",
        text=text,
        schema=LicenseInfo,
    )


def test_repeat_request_is_served_from_cache(make_client: MakeClient, tmp_path: Path) -> None:
    fake = make_client(lambda _schema, _text: INFO)
    llm = ClaudeClient(as_sdk(fake), cache=JsonCache(tmp_path / "cache"))

    first = parse(llm, "# MIT License")
    second = parse(llm, "# MIT License")

    assert first == second == INFO
    assert len(fake.beta.messages.calls) == 1
    assert llm.usage.cache_hits == 1


def test_cache_hits_do_not_count_toward_the_limit(make_client: MakeClient, tmp_path: Path) -> None:
    llm = ClaudeClient(
        as_sdk(make_client(lambda _schema, _text: INFO)),
        cache=JsonCache(tmp_path / "cache"),
        max_calls=1,
    )

    parse(llm, "same header")
    parse(llm, "same header")

    assert llm.usage.calls == 1


def test_limit_stops_further_calls(make_client: MakeClient) -> None:
    llm = ClaudeClient(as_sdk(make_client(lambda _schema, _text: INFO)), max_calls=1)

    parse(llm, "first")

    with pytest.raises(BudgetExceededError):
        parse(llm, "second")
    assert llm.usage.calls == 1


def test_changing_model_or_prompt_changes_the_key() -> None:
    original = request_key(model="m", system="s", tag="header", text="t", schema=LicenseInfo)

    assert original != request_key(model="other", system="s", tag="header", text="t", schema=LicenseInfo)
    assert original != request_key(model="m", system="changed", tag="header", text="t", schema=LicenseInfo)
