from collections.abc import Callable

import pytest

from tests.fakes import FakeClient, Responder


@pytest.fixture
def make_client() -> Callable[[Responder], FakeClient]:
    """Build a fake client from a responder function."""
    return FakeClient
