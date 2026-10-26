from datetime import date
from decimal import Decimal

import httpx
import pytest

from dfa_studio.domain.calendar import ProductionCalendar
from dfa_studio.extraction.drafting import build_draft
from dfa_studio.extraction.llm import HybridExtractor, OpenAICompatibleExtractor
from dfa_studio.extraction.rules import RuleExtractor

TODAY = date(2026, 10, 26)


def values_of(text: str) -> dict:
    return {key: item.value for key, item in RuleExtractor(today=TODAY).extract(text).values.items()}


def test_short_description() -> None:
    values = values_of(
        "Хотим привлечь до 300 млн рублей на полгода, номинал 1000 ₽, купон 18% годовых ежемесячно, только для квалов"
    )
    assert values == {
        "max_amount": Decimal("300000000"),
        "term_months": 6,
        "nominal": Decimal("1000"),
        "coupon_rate": Decimal("18"),
        "coupon_frequency": "monthly",
        "investors": "qualified_only",
    }


def test_detailed_description() -> None:
    values = values_of(
        "ИНН 0000000002. Выпуск на 500 млн на 1 год, номинал 10 000 руб, ставка 21,5% раз в квартал, "
        "размещение 15 декабря 2026, минимум 50% от объема, для всех инвесторов, перенос на следующий рабочий день, "
        "математическое округление, без досрочного погашения"
    )
    assert values["issuer_inn"] == "0000000002"
    assert values["min_amount"] == Decimal("250000000")
    assert values["coupon_rate"] == Decimal("21.5")
    assert values["issue_date"] == date(2026, 12, 15)
    assert values["investors"] == "all"
    assert values["early_redemption"] is False
    assert values["business_day_rule"] == "following"
    assert values["rounding_mode"] == "half_up"


def test_frequency_is_not_mistaken_for_term() -> None:
    values = values_of("Выплаты раз в полгода, срок 2 года, 15% годовых")
    assert values["coupon_frequency"] == "semiannual"
    assert values["term_months"] == 24


def test_evidence_points_to_source_text() -> None:
    extraction = RuleExtractor(today=TODAY).extract("Номинал 1000 ₽ и ставка 18%")
    assert extraction.values["nominal"].evidence == "Номинал 1000 ₽"
    assert extraction.values["coupon_rate"].evidence == "18%"


def test_draft_asks_only_for_missing_fields() -> None:
    extraction = RuleExtractor(today=TODAY).extract(
        "Привлечь до 300 млн на полгода, номинал 1000 ₽, 18% ежемесячно, только квалы"
    )
    draft = build_draft(extraction, ProductionCalendar(), TODAY, inn="0000000001")
    asked = {question.key for question in draft.questions}
    assert asked == {"min_amount", "issue_date", "rounding_mode", "business_day_rule", "early_redemption"}
    assert draft.issuer is not None and draft.issuer.code == "SVR"
    assert draft.values["price"].origin == "default"
    min_amount = next(q for q in draft.questions if q.key == "min_amount")
    assert [choice.value for choice in min_amount.choices] == ["90000000", "150000000", "300000000"]


def test_unknown_inn_is_reported() -> None:
    draft = build_draft(RuleExtractor(today=TODAY).extract("ИНН 1234567890"), ProductionCalendar(), TODAY)
    assert draft.issuer is None
    assert any("не найден" in note for note in draft.notes)
    assert any(question.key == "issuer_inn" for question in draft.questions)


def _fake_llm(content: str):
    def post(*_, **__):
        request = httpx.Request("POST", "http://llm/v1/chat/completions")
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]}, request=request)

    return post


def test_llm_values_override_rules_and_unverified_evidence_is_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    content = (
        '{"fields": {"coupon_rate": {"value": 19, "evidence": "девятнадцать процентов"},'
        ' "nominal": {"value": 5000, "evidence": "выдуманная цитата"}}}'
    )
    monkeypatch.setattr(httpx, "post", _fake_llm(content))
    llm = OpenAICompatibleExtractor("http://llm/v1", "model", "key", 5, "Тест")
    extraction = HybridExtractor(llm, RuleExtractor(today=TODAY)).extract(
        "Ставка девятнадцать процентов, номинал 1000 ₽"
    )
    assert extraction.provider == "hybrid"
    assert extraction.values["coupon_rate"].value == Decimal(19)
    assert extraction.values["nominal"].value == Decimal(1000)


def test_llm_failure_falls_back_to_rules(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_, **__):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", fail)
    llm = OpenAICompatibleExtractor("http://llm/v1", "model", "key", 5, "Тест")
    extraction = HybridExtractor(llm, RuleExtractor(today=TODAY)).extract("Номинал 1000 ₽")
    assert extraction.provider == "rules"
    assert extraction.notes
