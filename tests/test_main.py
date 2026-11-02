import json
import sys
from pathlib import Path

import pytest

from aithena.llm.client import ClaudeClient
from aithena.main import EXIT_BUDGET_REACHED, EXIT_FILE_ERRORS, EXIT_OK, main, parse_args, run
from tests.fakes import FakeClient, as_sdk
from tests.samples import MODELS, respond, write_fixtures


def make_llm(max_calls: int | None = None) -> ClaudeClient:
    return ClaudeClient(as_sdk(FakeClient(respond)), max_calls=max_calls)


def make_data(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    data.mkdir()
    write_fixtures(data)
    return data


def test_data_dir_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        parse_args([])

    assert "data_dir" in capsys.readouterr().err


def test_out_dir_defaults_to_output() -> None:
    args = parse_args(["data"])

    assert args.data_dir == Path("data")
    assert args.out_dir == Path("output")


def test_out_dir_can_be_given() -> None:
    assert parse_args(["data", "results"]).out_dir == Path("results")


def test_run_writes_all_outputs_and_returns_ok(tmp_path: Path) -> None:
    out = tmp_path / "out"

    code = run(make_data(tmp_path), out, make_llm(), MODELS)

    assert code == EXIT_OK
    assert json.loads((out / "errors.json").read_text(encoding="utf-8")) == {}
    assert (out / "rust" / "gpl_small.rs").exists()
    functions = json.loads((out / "functions.json").read_text(encoding="utf-8"))
    assert set(functions) == {"gpl_big.py", "perm.py"}


def test_run_stops_at_budget_and_keeps_finished_stage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out"

    # Four license calls fit in the budget; the function and Rust stage does not.
    code = run(make_data(tmp_path), out, make_llm(max_calls=5), MODELS)

    assert code == EXIT_BUDGET_REACHED
    assert (out / "licenses.json").exists()
    assert not (out / "functions.json").exists()
    assert "Stopped" in capsys.readouterr().err


def test_run_reports_failed_files_and_keeps_the_rest(tmp_path: Path) -> None:
    data = make_data(tmp_path)
    (data / "broken.py").write_bytes(b"\xff\xfe\x00")
    out = tmp_path / "out"

    code = run(data, out, make_llm(), MODELS)

    assert code == EXIT_FILE_ERRORS
    errors = json.loads((out / "errors.json").read_text(encoding="utf-8"))
    assert list(errors) == ["broken.py"]
    assert (out / "functions.json").exists()


def test_dry_run_prints_plan_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    data = make_data(tmp_path)
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["aithena", str(data), str(out), "--dry-run"])

    main()

    printed = capsys.readouterr().out
    assert "License calls needed: 4 (0 cached)" in printed
    assert not out.exists()
