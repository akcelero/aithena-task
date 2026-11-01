from pathlib import Path

import anthropic
from pydantic import BaseModel

from aithena.config.settings import Model


class ClaudeResponseError(RuntimeError):
    """Claude refused the request or returned no structured output."""


def parse_source[T: BaseModel](
    client: anthropic.Anthropic,
    *,
    model: Model,
    path: str | Path,
    system: str,
    tag: str,
    text: str,
    schema: type[T],
) -> T:
    """Send `text` (wrapped in <tag>) to Claude and return the output parsed into `schema`.

    Raises ClaudeResponseError if Claude refuses or returns no parsed output.
    """

    response = client.beta.messages.parse(
        model=model,
        max_tokens=16000,
        output_config={"effort": "low"},
        system=system,
        messages=[{"role": "user", "content": f"<{tag}>\n{text}\n</{tag}>"}],
        output_format=schema,
    )

    if response.stop_reason == "refusal":
        raise ClaudeResponseError(f"Claude declined to process {path}: {response.stop_details}")

    if response.parsed_output is None:
        raise ClaudeResponseError(
            f"No structured output for {path} (stop_reason={response.stop_reason})"
        )

    return response.parsed_output
