import json
import re
from typing import Any

import httpx

from dfa_studio.domain.fields import FIELDS, FIELDS_BY_KEY, FieldValue, Origin, coerce
from dfa_studio.extraction.base import Extraction
from dfa_studio.extraction.rules import RuleExtractor

SYSTEM_PROMPT = """Ты помогаешь подготовить выпуск цифровых финансовых активов (ЦФА).
Извлеки из описания пользователя только те параметры, которые в нём явно указаны.
Ничего не придумывай и не подставляй значения по умолчанию.
Верни JSON-объект вида {"fields": {"<ключ>": {"value": <значение>, "evidence": "<точная цитата из текста>"}}}.

Параметры:
%s

Правила форматов:
- денежные суммы в рублях числом без пробелов, например 300000000;
- ставка в процентах годовых числом, например 18.5;
- даты в формате ГГГГ-ММ-ДД;
- срок обращения в месяцах целым числом;
- для параметров с вариантами используй только перечисленные значения."""


def _describe_fields() -> str:
    lines = []
    for field in FIELDS:
        options = ", ".join(f"{choice.value} ({choice.label})" for choice in field.choices)
        suffix = f"; варианты: {options}" if options and field.kind in {"choice", "boolean"} else ""
        lines.append(f"- {field.key}: {field.label}, тип {field.kind}{suffix}")
    return "\n".join(lines)


def _parse_json(content: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError("ответ модели не содержит JSON")
    return json.loads(match.group(0))


class OpenAICompatibleExtractor:
    name = "llm"

    def __init__(self, base_url: str, model: str, api_key: str, timeout: float, label: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout
        self.label = label

    def _complete(self, text: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT % _describe_fields()},
                    {"role": "user", "content": text},
                ],
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return _parse_json(response.json()["choices"][0]["message"]["content"])

    def extract(self, text: str) -> Extraction:
        payload = self._complete(text)
        values: dict[str, FieldValue] = {}
        for key, item in (payload.get("fields") or {}).items():
            field = FIELDS_BY_KEY.get(key)
            if field is None or not isinstance(item, dict):
                continue
            evidence = str(item.get("evidence") or "").strip()
            if evidence and evidence.lower() not in text.lower():
                continue
            try:
                value = coerce(field, item.get("value"))
            except (ValueError, ArithmeticError):
                continue
            if field.choices and value not in {choice.value for choice in field.choices}:
                continue
            if value is not None:
                values[key] = FieldValue(value=value, origin=Origin.TEXT, evidence=evidence or None)
        return Extraction(provider=self.name, values=values)


class HybridExtractor:
    name = "hybrid"

    def __init__(self, llm: OpenAICompatibleExtractor, rules: RuleExtractor | None = None) -> None:
        self._llm = llm
        self._rules = rules or RuleExtractor()

    def extract(self, text: str) -> Extraction:
        baseline = self._rules.extract(text)
        try:
            primary = self._llm.extract(text)
        except (httpx.HTTPError, ValueError, KeyError) as error:
            return Extraction(
                provider=self._rules.name,
                values=baseline.values,
                notes=[f"Модель недоступна ({error.__class__.__name__}), использованы правила"],
            )
        merged = {**baseline.values, **primary.values}
        return Extraction(provider=self.name, values=merged)
