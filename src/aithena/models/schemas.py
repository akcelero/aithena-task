from typing import Literal

from pydantic import BaseModel, Field, computed_field


class LicenseInfo(BaseModel):
    copyright_holder: str | None = Field(
        description="Name of the copyright holder, or null if not stated."
    )
    license_name: str | None = Field(
        description="Common license name, e.g. 'MIT', 'GPL-3.0-or-later', or null if not stated."
    )
    license_type: Literal["permissive", "copyleft", "proprietary", "unknown"] = Field(
        description="permissive (MIT, BSD, Apache...), copyleft (GPL, LGPL, AGPL, MPL...), "
        "proprietary, or unknown if no license is identifiable."
    )


class Parameter(BaseModel):
    name: str = Field(description="Parameter name as written in the source.")
    type: str | None = Field(
        default=None,
        description="Declared type of the parameter, or null if the source gives no type.",
    )


class FunctionInfo(BaseModel):
    name: str = Field(description="Function name as written in the source.")
    parameters: list[Parameter] = Field(description="Declared parameters, in order.")

    @computed_field  # type: ignore[prop-decorator]  # mypy rejects this documented Pydantic pattern
    @property
    def argument_count(self) -> int:
        """Number of declared parameters. Saved in the output; not requested from the model."""

        return len(self.parameters)


class FunctionList(BaseModel):
    functions: list[FunctionInfo] = Field(description="Every function defined in the file.")


class RustRewrite(BaseModel):
    code: str = Field(description="The complete Rust source file, including any license header.")
