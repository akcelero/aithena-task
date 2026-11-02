import re
from pathlib import Path

from pydantic import BaseModel

from aithena.config.settings import Model, ModelConfig
from aithena.models.schemas import FunctionInfo, FunctionList, LicenseInfo, RustRewrite

MODELS = ModelConfig(for_extraction=Model.HAIKU_5_5, for_rust=Model.OPUS_5_5)

MIT_SOURCE = "# MIT License\n# Copyright (c) 2020 Ada\n\ndef only(x):\n    return x\n"
GPL_SMALL_SOURCE = "# GNU General Public License v3\n# Copyright (c) 2021 Bob\n\ndef one():\n    pass\n"
GPL_BIG_SOURCE = (
    "# GNU General Public License v3\n# Copyright (c) 2021 Bob\n\n"
    "def a():\n    pass\n\ndef b():\n    pass\n\ndef c():\n    pass\n"
)
PROPRIETARY_SOURCE = "# Copyright ACME. All rights reserved.\n\ndef secret():\n    pass\n"


def respond(schema: type[BaseModel], text: str) -> BaseModel:
    """Answer like the real model would for the fixture files in this module."""

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
