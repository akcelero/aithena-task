import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel

type JsonValue = dict[str, JsonValue] | list[JsonValue] | str | int | float | bool | None


class ResultWriter[T](ABC):
    """Writes data of type T to a destination fixed when the writer is created."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @abstractmethod
    def write(self, data: T) -> Path:
        """Write data and return the path it was written to."""


class JsonWriter(ResultWriter[JsonValue]):
    """Writes data as pretty-printed JSON to self.path."""

    def write(self, data: JsonValue) -> Path:
        """Write data as JSON and return self.path."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        return self.path


class RustWriter(ResultWriter[Mapping[str, str]]):
    """Writes each Rust rewrite to self.path/<stem>.rs. self.path is the output directory."""

    def write(self, data: Mapping[str, str]) -> Path:
        """Write one .rs file per entry and return the output directory."""

        self.path.mkdir(parents=True, exist_ok=True)

        for name, code in data.items():
            (self.path / f"{Path(name).stem}.rs").write_text(code + "\n", encoding="utf-8")

        return self.path


def write_results(results: Mapping[str, BaseModel], writer: ResultWriter[JsonValue]) -> Path:
    """Convert {file name: model} to plain data keyed by file name, then hand it to the writer."""

    data: dict[str, JsonValue] = {name: item.model_dump() for name, item in results.items()}

    return writer.write(data)
