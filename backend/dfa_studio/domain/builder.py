from decimal import Decimal
from typing import Any

from dfa_studio.domain.calendar import ProductionCalendar, add_months
from dfa_studio.domain.fields import FIELDS, FIELDS_BY_KEY, coerce
from dfa_studio.domain.spec import (
    Allocation,
    BusinessDayRule,
    CouponFrequency,
    InvestorAccess,
    Issuer,
    IssueSpec,
    RoundingMode,
)


class SpecError(ValueError):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("; ".join(f"{key}: {message}" for key, message in errors.items()))
        self.errors = errors


def missing_fields(values: dict[str, Any]) -> list[str]:
    return [
        field.key
        for field in FIELDS
        if values.get(field.key) is None and field.default is None and field.key != "price"
    ]


def normalize(values: dict[str, Any]) -> dict[str, Any]:
    result = {key: coerce(FIELDS_BY_KEY[key], raw) for key, raw in values.items() if key in FIELDS_BY_KEY}
    for field in FIELDS:
        if result.get(field.key) is None and field.default is not None:
            result[field.key] = coerce(field, field.default)
    if result.get("price") is None and result.get("nominal") is not None:
        result["price"] = result["nominal"]
    return result


def build_spec(
    raw_values: dict[str, Any],
    issuer: Issuer,
    issue_number: str,
    calendar: ProductionCalendar,
) -> IssueSpec:
    values = normalize(raw_values)
    missing = missing_fields(values)
    if missing:
        raise SpecError({key: "не заполнено" for key in missing})

    errors: dict[str, str] = {}
    nominal: Decimal = values["nominal"]
    if nominal <= 0:
        errors["nominal"] = "номинал должен быть больше нуля"
    if values["price"] <= 0:
        errors["price"] = "цена должна быть больше нуля"
    for key in ("min_amount", "max_amount"):
        if nominal > 0 and values[key] % nominal:
            errors[key] = "объём должен делиться на номинал без остатка"
    if values["min_amount"] > values["max_amount"]:
        errors["min_amount"] = "минимальный объём больше максимального"
    if not 0 < values["coupon_rate"] < 100:
        errors["coupon_rate"] = "ставка должна быть от 0 до 100% годовых"
    if values["term_months"] <= 0:
        errors["term_months"] = "срок должен быть положительным"
    if values["book_days"] <= 0:
        errors["book_days"] = "сбор заявок должен длиться хотя бы один день"
    if not calendar.is_business_day(values["issue_date"]):
        errors["issue_date"] = "дата размещения выпадает на нерабочий день"
    if errors:
        raise SpecError(errors)

    book_end = calendar.shift(values["issue_date"], -1)
    return IssueSpec(
        issue_number=issue_number,
        issuer=issuer,
        nominal=nominal,
        price=values["price"],
        min_quantity=int(values["min_amount"] / nominal),
        max_quantity=int(values["max_amount"] / nominal),
        book_start=calendar.shift(book_end, -(values["book_days"] - 1)),
        book_end=book_end,
        issue_date=values["issue_date"],
        maturity_date=add_months(values["issue_date"], values["term_months"]),
        coupon_rate=values["coupon_rate"] / 100,
        coupon_frequency=CouponFrequency(values["coupon_frequency"]),
        business_day_rule=BusinessDayRule(values["business_day_rule"]),
        rounding_mode=RoundingMode(values["rounding_mode"]),
        early_redemption=values["early_redemption"],
        investors=InvestorAccess(values["investors"]),
        allocation=Allocation(values["allocation"]),
    )
