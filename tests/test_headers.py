import pytest

from aithena.extraction.headers import extract_header_comment


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("# a\n# b\n\nimport os\n", "# a\n# b"),
        ("// MIT License\n//\n\nfunction f() {}\n", "// MIT License\n//"),
        ("/* line one\n   line two */\nint x;\n", "/* line one\n   line two */"),
        ('"""Module doc."""\nimport os\n', '"""Module doc."""'),
        ("import os\n# not a header\n", ""),
        ("", ""),
    ],
)
def test_extract_header_comment(source: str, expected: str) -> None:
    assert extract_header_comment(source) == expected
