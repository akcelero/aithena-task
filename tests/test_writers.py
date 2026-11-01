import json
from pathlib import Path

import pytest

from aithena.models.schemas import LicenseInfo
from aithena.output.writers import JsonWriter, ResultWriter, RustWriter, write_results


def test_json_writer_creates_parent_folders_and_writes_json(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "out.json"

    written = JsonWriter(target).write({"a.py": {"license_name": "MIT"}})

    assert written == target
    assert json.loads(target.read_text(encoding="utf-8")) == {"a.py": {"license_name": "MIT"}}


def test_rust_writer_writes_one_file_per_stem(tmp_path: Path) -> None:
    out_dir = tmp_path / "rust"

    written = RustWriter(out_dir).write({"1.py": "fn main() {}"})

    assert written == out_dir
    assert (out_dir / "1.rs").read_text(encoding="utf-8") == "fn main() {}\n"


def test_write_results_serialises_models(tmp_path: Path) -> None:
    target = tmp_path / "licenses.json"
    info = LicenseInfo(copyright_holder="Ada", license_name="MIT", license_type="permissive")

    write_results({"a.py": info}, JsonWriter(target))

    assert json.loads(target.read_text(encoding="utf-8")) == {
        "a.py": {"copyright_holder": "Ada", "license_name": "MIT", "license_type": "permissive"}
    }


def test_result_writer_is_abstract(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        ResultWriter(tmp_path)  # type: ignore[abstract]
