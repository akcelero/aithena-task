from pathlib import Path

from aithena.config.settings import Model
from aithena.extraction.tasks import extract_license
from aithena.llm.client import ClaudeClient
from tests.fakes import as_sdk


def test_file_without_header_is_unknown_and_makes_no_call(make_client, tmp_path: Path) -> None:
    source = tmp_path / "bare.py"
    source.write_text("def f():\n    pass\n", encoding="utf-8")
    fake = make_client(lambda _schema, _text: None)
    llm = ClaudeClient(as_sdk(fake))

    info = extract_license(llm, Model.HAIKU_5_5, source)

    assert info.license_type == "unknown"
    assert fake.beta.messages.calls == []
