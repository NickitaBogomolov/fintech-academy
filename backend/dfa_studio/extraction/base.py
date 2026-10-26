from typing import Protocol

from pydantic import BaseModel

from dfa_studio.domain.fields import FieldValue


class Extraction(BaseModel):
    provider: str
    values: dict[str, FieldValue]
    notes: list[str] = []


class Extractor(Protocol):
    name: str

    def extract(self, text: str) -> Extraction: ...
