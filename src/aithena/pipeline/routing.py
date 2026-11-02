from pathlib import Path

import anthropic

from aithena.config.settings import ModelConfig
from aithena.extraction.tasks import extract_functions, extract_license, rewrite_in_rust
from aithena.llm.client import ClaudeClient, ClaudeResponseError
from aithena.models.schemas import FunctionList, LicenseInfo

RUST_REWRITE_MAX_FUNCTIONS = 2

# Errors that affect one file only. Anything else is a bug or a config problem and should stop the run.
FILE_ERRORS = (anthropic.APIError, ClaudeResponseError, OSError, UnicodeDecodeError)


def extract_licenses(
    llm: ClaudeClient, models: ModelConfig, data_dir: Path
) -> tuple[dict[str, LicenseInfo], dict[str, str]]:
    """Return ({file name: LicenseInfo}, {file name: error}) for every data_dir/*.py file."""

    licenses: dict[str, LicenseInfo] = {}
    errors: dict[str, str] = {}

    for path in sorted(data_dir.glob("*.py")):
        try:
            licenses[path.name] = extract_license(llm, models.for_extraction, path)
        except FILE_ERRORS as exc:
            errors[path.name] = f"{type(exc).__name__}: {exc}"

    return licenses, errors


def process_licenses(
    llm: ClaudeClient,
    models: ModelConfig,
    licenses: dict[str, LicenseInfo],
    data_dir: Path,
) -> tuple[dict[str, FunctionList], dict[str, str], dict[str, str]]:
    """Route each file by license type.

    - permissive: extract function names and argument counts.
    - copyleft: count functions; if more than 2, extract them as above, otherwise rewrite in Rust.
    - proprietary/unknown: skipped.

    Returns ({file name: FunctionList}, {file name: Rust source}, {file name: error}).
    """

    functions: dict[str, FunctionList] = {}
    rust: dict[str, str] = {}
    errors: dict[str, str] = {}

    for name, info in licenses.items():
        path = data_dir / name

        try:
            if info.license_type == "permissive":
                functions[name] = extract_functions(llm, models.for_extraction, path)

            elif info.license_type == "copyleft":
                found = extract_functions(llm, models.for_extraction, path)

                if len(found.functions) > RUST_REWRITE_MAX_FUNCTIONS:
                    functions[name] = found
                else:
                    rust[name] = rewrite_in_rust(llm, models.for_rust, path)

        except FILE_ERRORS as exc:
            errors[name] = f"{type(exc).__name__}: {exc}"

    return functions, rust, errors
