import json
from functools import cache
from importlib import resources

from dfa_studio.domain.spec import Issuer


@cache
def _issuers() -> dict[str, Issuer]:
    raw = resources.files("dfa_studio.data").joinpath("registry.json").read_text(encoding="utf-8")
    return {item["inn"]: Issuer(**item) for item in json.loads(raw)}


def find_issuer(inn: str) -> Issuer | None:
    return _issuers().get(inn.strip())


def list_issuers() -> list[Issuer]:
    return list(_issuers().values())
