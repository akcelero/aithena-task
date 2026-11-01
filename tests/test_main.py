from pathlib import Path

import pytest

from aithena.main import parse_args


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
