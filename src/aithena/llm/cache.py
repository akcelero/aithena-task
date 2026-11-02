import hashlib
import json
from pathlib import Path

from pydantic import BaseModel


def request_key(*, model: str, system: str, tag: str, text: str, schema: type[BaseModel]) -> str:
    """Hash everything that shapes the answer, so a changed prompt, model or schema misses the cache."""

    payload = {
        "model": model,
        "system": system,
        "tag": tag,
        "text": text,
        "schema": schema.model_json_schema(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class JsonCache:
    """Stores one JSON file per request key in a directory."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def _file(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def contains(self, key: str) -> bool:
        return self._file(key).exists()

    def get[T: BaseModel](self, key: str, schema: type[T]) -> T | None:
        path = self._file(key)

        if not path.exists():
            return None

        return schema.model_validate_json(path.read_text(encoding="utf-8"))

    def put(self, key: str, value: BaseModel) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

        self._file(key).write_text(value.model_dump_json(), encoding="utf-8")
