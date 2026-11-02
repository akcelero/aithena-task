from pathlib import Path

from aithena.config.settings import Model
from aithena.extraction.headers import extract_header_comment
from aithena.llm.client import ClaudeClient
from aithena.models.schemas import FunctionList, LicenseInfo, RustRewrite

LICENSE_SYSTEM_PROMPT = (
    "You extract licensing information from the header comment of a source file. "
    "Identify the license even when only its boilerplate text is present (no explicit name). "
    "Use only what the text supports; return null for fields that are not stated."
)

FUNCTIONS_SYSTEM_PROMPT = (
    "You list the functions defined in a source file. Include every function or method "
    "definition (Python def, JavaScript function declarations/expressions, arrow functions "
    "assigned to names). For each function list its declared parameters (names only, not "
    "call arguments), in order, with the declared type if the source gives one, otherwise null. "
    "Return an empty list if the file defines no functions."
)

REWRITE_SYSTEM_PROMPT = (
    "You rewrite a source file in Rust, preserving its behaviour. Keep the original copyright "
    "and license notice as Rust comments at the top of the file, unchanged in substance, "
    "since the code is a derivative of the original. Return only the Rust source."
)


def extract_license(llm: ClaudeClient, model: Model, path: Path) -> LicenseInfo:
    """Send the file's header comment to Claude and return the extracted license info."""

    header = extract_header_comment(path.read_text(encoding="utf-8"))

    if not header.strip():
        return LicenseInfo(copyright_holder=None, license_name=None, license_type="unknown")

    return llm.parse(
        model=model,
        path=path,
        system=LICENSE_SYSTEM_PROMPT,
        tag="header",
        text=header,
        schema=LicenseInfo,
    )


def extract_functions(llm: ClaudeClient, model: Model, path: Path) -> FunctionList:
    """Send the whole file to Claude and return its function names with argument counts."""

    source = path.read_text(encoding="utf-8")

    return llm.parse(
        model=model,
        path=path,
        system=FUNCTIONS_SYSTEM_PROMPT,
        tag="source",
        text=source,
        schema=FunctionList,
    )


def rewrite_in_rust(llm: ClaudeClient, model: Model, path: Path) -> str:
    """Send the whole file to Claude and return its Rust rewrite."""

    source = path.read_text(encoding="utf-8")

    result = llm.parse(
        model=model,
        path=path,
        system=REWRITE_SYSTEM_PROMPT,
        tag="source",
        text=source,
        schema=RustRewrite,
    )

    return result.code
