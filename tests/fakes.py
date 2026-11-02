from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import anthropic
from pydantic import BaseModel

# Decides what the fake Claude returns: receives the requested schema and the prompt text.
Responder = Callable[[type[BaseModel], str], BaseModel | None]


class FakeMessages:
    """Stands in for client.beta.messages and records every request."""

    def __init__(self, respond: Responder) -> None:
        self._respond = respond
        self.calls: list[tuple[str, type[BaseModel]]] = []

    def parse(
        self,
        *,
        model: str,
        output_format: type[BaseModel],
        messages: list[dict[str, Any]],
        **_: Any,
    ) -> SimpleNamespace:
        self.calls.append((model, output_format))
        parsed = self._respond(output_format, messages[0]["content"])
        usage = SimpleNamespace(input_tokens=100, output_tokens=20)
        return SimpleNamespace(stop_reason="end_turn", stop_details=None, parsed_output=parsed, usage=usage)


class FakeClient:
    """Stands in for anthropic.Anthropic with only the parts the app uses."""

    def __init__(self, respond: Responder) -> None:
        self.beta = SimpleNamespace(messages=FakeMessages(respond))


def as_sdk(fake: FakeClient) -> anthropic.Anthropic:
    """FakeClient implements the part of anthropic.Anthropic that the app uses, so the cast is safe."""
    return cast("anthropic.Anthropic", fake)
