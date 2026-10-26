from datetime import date
from decimal import Decimal

import pytest

from dfa_studio.domain.builder import SpecError, build_spec
from dfa_studio.domain.calendar import ProductionCalendar, add_months
from dfa_studio.domain.schedule import build_schedule, coupon_amount
from dfa_studio.domain.spec import RoundingMode


def test_holidays_and_weekends(calendar: ProductionCalendar) -> None:
    assert not calendar.is_business_day(date(2027, 1, 4))
    assert not calendar.is_business_day(date(2027, 5, 15))
    assert calendar.following(date(2027, 5, 15)) == date(2027, 5, 17)
    assert calendar.preceding(date(2027, 5, 15)) == date(2027, 5, 14)


def test_extra_workday_overrides_weekend() -> None:
    calendar = ProductionCalendar(extra_workdays=[date(2027, 5, 15)])
    assert calendar.is_business_day(date(2027, 5, 15))


def test_add_months_clamps_to_month_end() -> None:
    assert add_months(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert add_months(date(2026, 12, 15), 6) == date(2027, 6, 15)


def test_spec_derives_quantities_and_dates(spec) -> None:
    assert spec.max_quantity == 300_000
    assert spec.min_quantity == 100_000
    assert spec.price == Decimal("1000")
    assert spec.book_end == date(2026, 12, 14)
    assert spec.book_start == date(2026, 12, 8)
    assert spec.maturity_date == date(2027, 6, 15)


def test_monthly_schedule_matches_reference(spec, calendar) -> None:
    schedule = build_schedule(spec, calendar)
    coupons = [period.coupon for period in schedule.periods]
    assert coupons == [Decimal(x) for x in ("15.29", "15.29", "13.81", "15.29", "14.79", "15.29")]
    assert schedule.periods[4].payment_date == date(2027, 5, 17)
    assert schedule.periods[4].shifted
    assert schedule.periods[-1].principal == Decimal("1000")
    assert schedule.total_coupon == Decimal("89.76")


def test_rounding_down_differs_by_kopecks() -> None:
    assert coupon_amount(Decimal(1000), Decimal("0.18"), 31, RoundingMode.HALF_UP) == Decimal("15.29")
    assert coupon_amount(Decimal(1000), Decimal("0.18"), 31, RoundingMode.DOWN) == Decimal("15.28")


def test_amount_must_be_multiple_of_nominal(raw_values, issuer, calendar) -> None:
    raw_values["max_amount"] = "300000500"
    with pytest.raises(SpecError) as error:
        build_spec(raw_values, issuer, "X", calendar)
    assert "max_amount" in error.value.errors


def test_missing_fields_reported(issuer, calendar) -> None:
    with pytest.raises(SpecError) as error:
        build_spec({"nominal": "1000"}, issuer, "X", calendar)
    assert {"coupon_rate", "issue_date", "investors"} <= error.value.errors.keys()
