from pathlib import Path

import pytest
from pydantic import BaseModel

from aithena.config.settings import Model
from aithena.llm.client import ClaudeClient, ClaudeResponseError
from aithena.models.schemas import FunctionList, RustRewrite
from aithena.pipeline.routing import extract_licenses, process_licenses
from tests.fakes import as_sdk
from tests.samples import MIT_SOURCE, MODELS, respond, write_fixtures


def test_extract_licenses_classifies_each_file(make_llm, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    llm = make_llm(respond)

    licenses, errors = extract_licenses(llm, MODELS, tmp_path)

    assert errors == {}
    assert {name: info.license_type for name, info in licenses.items()} == {
        "gpl_big.py": "copyleft",
        "gpl_small.py": "copyleft",
        "perm.py": "permissive",
        "prop.py": "proprietary",
    }


def test_process_licenses_routes_by_license_and_function_count(make_llm, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    llm = make_llm(respond)
    licenses, _ = extract_licenses(llm, MODELS, tmp_path)

    functions, rust, errors = process_licenses(llm, MODELS, licenses, tmp_path)

    assert errors == {}
    assert set(functions) == {"perm.py", "gpl_big.py"}
    assert rust == {"gpl_small.py": "fn converted() {}"}
    assert "prop.py" not in functions
    assert "prop.py" not in rust


def test_undecodable_file_is_reported_and_others_still_processed(make_llm, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    (tmp_path / "broken.py").write_bytes(b"\xff\xfe\x00 not utf-8")
    llm = make_llm(respond)

    licenses, errors = extract_licenses(llm, MODELS, tmp_path)

    assert "broken.py" not in licenses
    assert errors["broken.py"].startswith("UnicodeDecodeError")
    assert set(licenses) == {"gpl_big.py", "gpl_small.py", "perm.py", "prop.py"}


def test_api_failure_on_one_file_does_not_stop_the_rest(make_llm, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    (tmp_path / "fail.py").write_text(MIT_SOURCE + "# FAIL\n", encoding="utf-8")

    def respond_with_failure(schema: type[BaseModel], text: str) -> BaseModel:
        if schema is FunctionList and "FAIL" in text:
            raise ClaudeResponseError("No structured output for fail.py")
        return respond(schema, text)

    llm = make_llm(respond_with_failure)
    licenses, license_errors = extract_licenses(llm, MODELS, tmp_path)

    functions, rust, process_errors = process_licenses(llm, MODELS, licenses, tmp_path)

    assert license_errors == {}
    assert process_errors == {"fail.py": "ClaudeResponseError: No structured output for fail.py"}
    assert "perm.py" in functions
    assert "gpl_big.py" in functions
    assert "gpl_small.py" in rust


def test_unexpected_errors_are_not_swallowed(make_llm, tmp_path: Path) -> None:
    write_fixtures(tmp_path)

    def respond_with_bug(_schema: type, _text: str) -> object:
        raise KeyError("bug in the pipeline")

    llm = make_llm(respond_with_bug)

    with pytest.raises(KeyError):
        extract_licenses(llm, MODELS, tmp_path)


def test_models_are_routed_per_stage(make_client, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    fake = make_client(respond)
    llm = ClaudeClient(as_sdk(fake))
    licenses, _ = extract_licenses(llm, MODELS, tmp_path)
    fake.beta.messages.calls.clear()

    process_licenses(llm, MODELS, licenses, tmp_path)

    rust_models = [model for model, schema in fake.beta.messages.calls if schema is RustRewrite]
    other_models = [model for model, schema in fake.beta.messages.calls if schema is not RustRewrite]
    assert rust_models == [Model.OPUS_5_5]
    assert set(other_models) == {Model.HAIKU_5_5}
