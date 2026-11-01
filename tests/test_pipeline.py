import re
from pathlib import Path

from aithena.config.settings import Model, ModelConfig
from aithena.models.schemas import FunctionInfo, FunctionList, LicenseInfo, RustRewrite
from aithena.pipeline.routing import extract_licenses, process_licenses

MODELS = ModelConfig(for_extraction=Model.HAIKU_5_5, for_rust=Model.OPUS_5_5)

MIT_SOURCE = "# MIT License\n# Copyright (c) 2020 Ada\n\ndef only(x):\n    return x\n"
GPL_SMALL_SOURCE = "# GNU General Public License v3\n# Copyright (c) 2021 Bob\n\ndef one():\n    pass\n"
GPL_BIG_SOURCE = (
    "# GNU General Public License v3\n# Copyright (c) 2021 Bob\n\n"
    "def a():\n    pass\n\ndef b():\n    pass\n\ndef c():\n    pass\n"
)
PROPRIETARY_SOURCE = "# Copyright ACME. All rights reserved.\n\ndef secret():\n    pass\n"


def respond(schema: type, text: str) -> object:
    """Answer like the real model would for the fixture files used below."""
    if schema is LicenseInfo:
        if "MIT License" in text:
            return LicenseInfo(copyright_holder="Ada", license_name="MIT", license_type="permissive")

        if "GNU General Public License" in text:
            return LicenseInfo(copyright_holder="Bob", license_name="GPL-3.0", license_type="copyleft")

        return LicenseInfo(copyright_holder="ACME", license_name=None, license_type="proprietary")

    if schema is FunctionList:
        names = re.findall(r"^def (\w+)\(", text, re.MULTILINE)

        return FunctionList(functions=[FunctionInfo(name=n, parameters=[]) for n in names])

    return RustRewrite(code="fn converted() {}")


def write_fixtures(data_dir: Path) -> None:
    (data_dir / "perm.py").write_text(MIT_SOURCE, encoding="utf-8")
    (data_dir / "gpl_small.py").write_text(GPL_SMALL_SOURCE, encoding="utf-8")
    (data_dir / "gpl_big.py").write_text(GPL_BIG_SOURCE, encoding="utf-8")
    (data_dir / "prop.py").write_text(PROPRIETARY_SOURCE, encoding="utf-8")


def test_extract_licenses_classifies_each_file(make_client, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    client = make_client(respond)

    licenses = extract_licenses(client, MODELS, tmp_path)

    assert {name: info.license_type for name, info in licenses.items()} == {
        "gpl_big.py": "copyleft",
        "gpl_small.py": "copyleft",
        "perm.py": "permissive",
        "prop.py": "proprietary",
    }


def test_process_licenses_routes_by_license_and_function_count(make_client, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    client = make_client(respond)
    licenses = extract_licenses(client, MODELS, tmp_path)

    functions, rust = process_licenses(client, MODELS, licenses, tmp_path)

    assert set(functions) == {"perm.py", "gpl_big.py"}
    assert rust == {"gpl_small.py": "fn converted() {}"}
    assert "prop.py" not in functions
    assert "prop.py" not in rust


def test_models_are_routed_per_stage(make_client, tmp_path: Path) -> None:
    write_fixtures(tmp_path)
    client = make_client(respond)
    licenses = extract_licenses(client, MODELS, tmp_path)
    client.beta.messages.calls.clear()

    process_licenses(client, MODELS, licenses, tmp_path)

    rust_models = [model for model, schema in client.beta.messages.calls if schema is RustRewrite]
    other_models = [model for model, schema in client.beta.messages.calls if schema is not RustRewrite]
    assert rust_models == [Model.OPUS_5_5]
    assert set(other_models) == {Model.HAIKU_5_5}
