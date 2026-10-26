import json
from datetime import UTC, date, datetime
from functools import cache
from importlib import resources
from typing import Any

from dfa_studio.domain.fields import FIELDS, FIELDS_BY_KEY, coerce, serialize
from dfa_studio.extraction.base import Extractor


@cache
def load_cases() -> dict[str, Any]:
    raw = resources.files("dfa_studio.data").joinpath("benchmark.json").read_text(encoding="utf-8")
    return json.loads(raw)


def benchmark_today() -> date:
    return date.fromisoformat(load_cases()["today"])


def run_benchmark(extractor: Extractor, provider_label: str) -> dict[str, Any]:
    dataset = load_cases()
    per_field = {field.key: {"label": field.label, "expected": 0, "correct": 0} for field in FIELDS}
    expected_total = correct_total = extracted_total = exact_cases = 0
    failures: list[dict[str, Any]] = []

    for case in dataset["cases"]:
        extracted = {key: item.value for key, item in extractor.extract(case["text"]).values.items()}
        extracted_total += len(extracted)
        errors = []
        for key, raw in case["expected"].items():
            expected = coerce(FIELDS_BY_KEY[key], raw)
            per_field[key]["expected"] += 1
            expected_total += 1
            actual = extracted.get(key)
            if actual == expected:
                per_field[key]["correct"] += 1
                correct_total += 1
            else:
                errors.append(
                    {
                        "field": FIELDS_BY_KEY[key].label,
                        "expected": serialize(expected),
                        "actual": None if actual is None else serialize(actual),
                    }
                )
        extra = sorted(set(extracted) - set(case["expected"]))
        for key in extra:
            errors.append(
                {"field": FIELDS_BY_KEY[key].label, "expected": None, "actual": serialize(extracted[key])}
            )
        if not errors:
            exact_cases += 1
        else:
            failures.append({"text": case["text"], "errors": errors})

    return {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset": dataset["name"],
        "source": dataset["source"],
        "provider": provider_label,
        "cases": len(dataset["cases"]),
        "exact_cases": exact_cases,
        "fields_expected": expected_total,
        "fields_correct": correct_total,
        "recall": round(correct_total / expected_total, 4) if expected_total else 0,
        "precision": round(correct_total / extracted_total, 4) if extracted_total else 0,
        "per_field": [dict(key=key, **value) for key, value in per_field.items() if value["expected"]],
        "failures": failures,
    }
