from dataclasses import dataclass
from pathlib import Path

from aithena.config.settings import ModelConfig
from aithena.extraction.headers import extract_header_comment
from aithena.extraction.tasks import LICENSE_SYSTEM_PROMPT
from aithena.llm.cache import JsonCache, request_key
from aithena.models.schemas import LicenseInfo
from aithena.pipeline.routing import FILE_ERRORS

# After the license call a file needs at most two more: functions, then a Rust rewrite.
MAX_CALLS_AFTER_LICENSE = 2


@dataclass(frozen=True)
class RunPlan:
    files: int
    unreadable: int
    license_calls: int
    cached_license_calls: int
    worst_case_calls: int


def plan_run(data_dir: Path, cache: JsonCache, models: ModelConfig) -> RunPlan:
    """Estimate the API calls a run needs, without making any.

    The license calls are exact, since they depend only on the file. Later calls depend on
    Claude's answers, so the total is an upper bound.
    """

    files = sorted(data_dir.glob("*.py"))
    unreadable = 0
    with_header = 0
    license_calls = 0
    cached = 0

    for path in files:
        try:
            header = extract_header_comment(path.read_text(encoding="utf-8"))
        except FILE_ERRORS:
            unreadable += 1
            continue

        if not header.strip():
            continue

        with_header += 1
        key = request_key(
            model=models.for_extraction,
            system=LICENSE_SYSTEM_PROMPT,
            tag="header",
            text=header,
            schema=LicenseInfo,
        )

        if cache.contains(key):
            cached += 1
        else:
            license_calls += 1

    return RunPlan(
        files=len(files),
        unreadable=unreadable,
        license_calls=license_calls,
        cached_license_calls=cached,
        worst_case_calls=license_calls + MAX_CALLS_AFTER_LICENSE * with_header,
    )
