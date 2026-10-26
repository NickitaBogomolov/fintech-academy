from datetime import date

import pytest

from dfa_studio.domain.builder import build_spec
from dfa_studio.domain.calendar import ProductionCalendar
from dfa_studio.domain.spec import Issuer, IssueSpec


@pytest.fixture
def calendar() -> ProductionCalendar:
    return ProductionCalendar()


@pytest.fixture
def issuer() -> Issuer:
    return Issuer(
        inn="0000000001",
        ogrn="0000000000001",
        full_name="Общество с ограниченной ответственностью «Северный Ритейл»",
        short_name="ООО «Северный Ритейл»",
        code="SVR",
        address="г. Москва, ул. Примерная, д. 1",
        director="Генеральный директор Иванов Иван Иванович",
        website="https://example.org/cfa",
    )


@pytest.fixture
def raw_values() -> dict:
    return {
        "issuer_inn": "0000000001",
        "nominal": "1000",
        "max_amount": "300000000",
        "min_amount": "100000000",
        "issue_date": date(2026, 12, 15),
        "term_months": 6,
        "coupon_rate": "18",
        "coupon_frequency": "monthly",
        "rounding_mode": "half_up",
        "business_day_rule": "following",
        "early_redemption": False,
        "investors": "qualified_only",
    }


@pytest.fixture
def spec(raw_values: dict, issuer: Issuer, calendar: ProductionCalendar) -> IssueSpec:
    return build_spec(raw_values, issuer, "SVR-001-2026", calendar)
