from collections.abc import Callable

import pytest

from aithena.llm.client import ClaudeClient
from tests.fakes import FakeClient, Responder, as_sdk


@pytest.fixture
def make_client() -> Callable[[Responder], FakeClient]:
    """Build a fake SDK client from a responder function."""
    return FakeClient


@pytest.fixture
def make_llm() -> Callable[[Responder], ClaudeClient]:
    """Build the app's ClaudeClient on top of a fake SDK client, with no cache or limit."""
    return lambda respond: ClaudeClient(as_sdk(FakeClient(respond)))
