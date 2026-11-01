from pathlib import Path

import anthropic

from aithena.config.settings import ModelConfig
from aithena.extraction.tasks import extract_functions, extract_license, rewrite_in_rust
from aithena.models.schemas import FunctionList, LicenseInfo

RUST_REWRITE_MAX_FUNCTIONS = 2


def extract_licenses(
    client: anthropic.Anthropic, models: ModelConfig, data_dir: Path
) -> dict[str, LicenseInfo]:
    """Return {file name: LicenseInfo} for every data_dir/*.py file."""

    return {
        path.name: extract_license(client, models.for_extraction, path)
        for path in sorted(data_dir.glob("*.py"))
    }


def process_licenses(
    client: anthropic.Anthropic,
    models: ModelConfig,
    licenses: dict[str, LicenseInfo],
    data_dir: Path,
) -> tuple[dict[str, FunctionList], dict[str, str]]:
    """Route each file by license type.

    - permissive: extract function names and argument counts.
    - copyleft: count functions; if more than 2, extract them as above, otherwise rewrite in Rust.
    - proprietary/unknown: skipped.

    Returns ({file name: FunctionList}, {file name: Rust source}).
    """

    functions: dict[str, FunctionList] = {}
    rust: dict[str, str] = {}

    for name, info in licenses.items():
        path = data_dir / name

        if info.license_type == "permissive":
            functions[name] = extract_functions(client, models.for_extraction, path)

        elif info.license_type == "copyleft":
            found = extract_functions(client, models.for_extraction, path)

            if len(found.functions) > RUST_REWRITE_MAX_FUNCTIONS:
                functions[name] = found
            else:
                rust[name] = rewrite_in_rust(client, models.for_rust, path)

    return functions, rust
