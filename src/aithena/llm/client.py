from dataclasses import dataclass
from pathlib import Path

import anthropic
from pydantic import BaseModel

from aithena.config.settings import Model
from aithena.llm.cache import JsonCache, request_key


class ClaudeResponseError(RuntimeError):
    """Claude refused the request or returned no structured output."""


class BudgetExceededError(Exception):
    """The run reached its call limit. Cached results are kept, so a re-run picks up where it stopped."""


@dataclass
class Usage:
    calls: int = 0
    cache_hits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


class ClaudeClient:
    """Calls Claude with caching, a hard call limit and usage tracking."""

    def __init__(
        self,
        client: anthropic.Anthropic,
        cache: JsonCache | None = None,
        max_calls: int | None = None,
    ) -> None:
        self._client = client
        self._cache = cache
        self._max_calls = max_calls
        self.usage = Usage()

    def parse[T: BaseModel](
        self,
        *,
        model: Model,
        path: str | Path,
        system: str,
        tag: str,
        text: str,
        schema: type[T],
    ) -> T:
        """Send `text` (wrapped in <tag>) to Claude and return the output parsed into `schema`.

        Cached answers are returned without a call and do not count toward the limit.
        Raises BudgetExceededError when the limit is reached, and ClaudeResponseError if Claude
        refuses or returns no parsed output.
        """

        key = request_key(model=model, system=system, tag=tag, text=text, schema=schema)

        if self._cache is not None:
            cached = self._cache.get(key, schema)

            if cached is not None:
                self.usage.cache_hits += 1
                return cached

        if self._max_calls is not None and self.usage.calls >= self._max_calls:
            raise BudgetExceededError(f"call limit of {self._max_calls} reached")

        response = self._client.beta.messages.parse(
            model=model,
            max_tokens=16000,
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": f"<{tag}>\n{text}\n</{tag}>"}],
            output_format=schema,
        )

        self.usage.calls += 1
        self.usage.input_tokens += response.usage.input_tokens
        self.usage.output_tokens += response.usage.output_tokens

        if response.stop_reason == "refusal":
            raise ClaudeResponseError(f"Claude declined to process {path}: {response.stop_details}")

        if response.parsed_output is None:
            raise ClaudeResponseError(
                f"No structured output for {path} (stop_reason={response.stop_reason})"
            )

        if self._cache is not None:
            self._cache.put(key, response.parsed_output)

        return response.parsed_output
