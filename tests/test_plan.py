from pathlib import Path

from aithena.config.settings import Model, ModelConfig
from aithena.extraction.headers import extract_header_comment
from aithena.extraction.tasks import LICENSE_SYSTEM_PROMPT
from aithena.llm.cache import JsonCache, request_key
from aithena.models.schemas import LicenseInfo
from aithena.pipeline.plan import plan_run

MODELS = ModelConfig(for_extraction=Model.HAIKU_5_5, for_rust=Model.OPUS_5_5)
MIT = "# MIT License\n# Copyright (c) 2020 Ada\n\ndef only(x):\n    return x\n"
GPL = "# GNU General Public License v3\n\ndef f():\n    pass\n"


def test_plan_counts_license_calls_and_cached_answers(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "a.py").write_text(MIT, encoding="utf-8")
    (data / "b.py").write_text(GPL, encoding="utf-8")
    (data / "c.py").write_text("def bare():\n    pass\n", encoding="utf-8")

    cache = JsonCache(tmp_path / "cache")
    key_b = request_key(
        model=MODELS.for_extraction,
        system=LICENSE_SYSTEM_PROMPT,
        tag="header",
        text=extract_header_comment(GPL),
        schema=LicenseInfo,
    )
    cache.put(key_b, LicenseInfo(copyright_holder=None, license_name="GPL-3.0", license_type="copyleft"))

    plan = plan_run(data, cache, MODELS)

    assert plan.files == 3
    assert plan.unreadable == 0
    assert plan.license_calls == 1  # a.py; b.py is cached; c.py has no header
    assert plan.cached_license_calls == 1
    assert plan.worst_case_calls == 1 + 2 * 2  # two files with headers, up to two more calls each


def test_unreadable_files_are_counted_not_fatal(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "bad.py").write_bytes(b"\xff\xfe\x00")

    plan = plan_run(data, JsonCache(tmp_path / "cache"), MODELS)

    assert plan.files == 1
    assert plan.unreadable == 1
    assert plan.worst_case_calls == 0
