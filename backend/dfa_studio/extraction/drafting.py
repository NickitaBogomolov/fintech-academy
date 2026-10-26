from datetime import date, timedelta
from decimal import Decimal

from pydantic import BaseModel

from dfa_studio.domain.calendar import ProductionCalendar
from dfa_studio.domain.fields import FIELDS, Choice, FieldKind, FieldValue, Origin, coerce
from dfa_studio.domain.spec import Issuer
from dfa_studio.extraction.base import Extraction, Extractor
from dfa_studio.extraction.llm import HybridExtractor, OpenAICompatibleExtractor
from dfa_studio.extraction.rules import RuleExtractor
from dfa_studio.registry import find_issuer
from dfa_studio.settings import Settings


class Question(BaseModel):
    key: str
    text: str
    hint: str | None
    kind: FieldKind
    choices: list[Choice]


class Draft(BaseModel):
    provider: str
    values: dict[str, FieldValue]
    questions: list[Question]
    issuer: Issuer | None
    notes: list[str]


def make_extractor(settings: Settings) -> Extractor:
    if settings.llm_provider == "openai":
        return HybridExtractor(
            OpenAICompatibleExtractor(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                timeout=settings.llm_timeout,
                label=settings.llm_label,
            )
        )
    return RuleExtractor()


def _format_rub(amount: Decimal) -> str:
    return f"{amount:,.0f}".replace(",", " ") + " ₽"


def _suggestions(
    key: str, values: dict[str, FieldValue], calendar: ProductionCalendar, today: date
) -> list[Choice]:
    if key == "min_amount" and "max_amount" in values:
        maximum = Decimal(values["max_amount"].value)
        nominal = Decimal(values["nominal"].value) if "nominal" in values else Decimal(1)
        options = []
        for share, label in ((Decimal("0.3"), "30%"), (Decimal("0.5"), "50%"), (Decimal(1), "100%")):
            amount = (maximum * share / nominal).to_integral_value() * nominal
            options.append(
                Choice(value=format(amount.normalize(), "f"), label=f"{label} — {_format_rub(amount)}")
            )
        return options
    if key == "issue_date":
        options = []
        for weeks in (2, 3, 4):
            day = calendar.following(today + timedelta(weeks=weeks))
            options.append(Choice(value=day.isoformat(), label=day.strftime("%d.%m.%Y")))
        return options
    return []


def build_draft(
    extraction: Extraction,
    calendar: ProductionCalendar,
    today: date,
    inn: str | None = None,
    answers: dict[str, object] | None = None,
) -> Draft:
    values = dict(extraction.values)
    fields = {field.key: field for field in FIELDS}
    if inn and "issuer_inn" not in values:
        values["issuer_inn"] = FieldValue(value=inn.strip(), origin=Origin.ANSWER)
    for key, raw in (answers or {}).items():
        if key in fields and raw not in (None, ""):
            values[key] = FieldValue(value=coerce(fields[key], raw), origin=Origin.ANSWER)

    notes = list(extraction.notes)
    issuer = None
    if "issuer_inn" in values:
        issuer = find_issuer(str(values["issuer_inn"].value))
        if issuer is None:
            notes.append(f"ИНН {values['issuer_inn'].value} не найден в реестре")
            values.pop("issuer_inn")

    for field in FIELDS:
        if field.key not in values and field.default is not None:
            values[field.key] = FieldValue(value=coerce(field, field.default), origin=Origin.DEFAULT)
    if "price" not in values and "nominal" in values:
        values["price"] = FieldValue(value=values["nominal"].value, origin=Origin.DEFAULT)

    questions = [
        Question(
            key=field.key,
            text=field.question,
            hint=field.hint,
            kind=field.kind,
            choices=_suggestions(field.key, values, calendar, today) or field.choices,
        )
        for field in FIELDS
        if field.key not in values
    ]
    ordered = {field.key: values[field.key] for field in FIELDS if field.key in values}
    return Draft(
        provider=extraction.provider, values=ordered, questions=questions, issuer=issuer, notes=notes
    )
