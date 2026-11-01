from dataclasses import dataclass
from enum import StrEnum


class Model(StrEnum):
    FABLE_5_1 = "claude-fable-5-1"
    OPUS_5_5 = "claude-opus-5-5"
    SONNET_5_5 = "claude-sonnet-5-5"
    HAIKU_5_5 = "claude-haiku-5-5"


@dataclass(frozen=True)
class ModelConfig:
    for_extraction: Model
    for_rust: Model


DEFAULT_MODELS = ModelConfig(
    for_extraction=Model.HAIKU_5_5,
    for_rust=Model.OPUS_5_5,
)
