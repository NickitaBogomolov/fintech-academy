from dataclasses import dataclass
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from dfa_studio.domain.calendar import ProductionCalendar, add_months
from dfa_studio.domain.spec import BusinessDayRule, IssueSpec, RoundingMode

DAYS_IN_YEAR = 365
KOPECK = Decimal("0.01")


@dataclass(frozen=True)
class Period:
    number: int
    start: date
    end: date
    days: int
    coupon: Decimal
    principal: Decimal
    payment_date: date

    @property
    def shifted(self) -> bool:
        return self.payment_date != self.end

    @property
    def payment(self) -> Decimal:
        return self.coupon + self.principal


@dataclass(frozen=True)
class Schedule:
    periods: tuple[Period, ...]

    @property
    def total_coupon(self) -> Decimal:
        return sum((p.coupon for p in self.periods), Decimal(0))

    @property
    def total_payment(self) -> Decimal:
        return sum((p.payment for p in self.periods), Decimal(0))


def coupon_amount(nominal: Decimal, rate: Decimal, days: int, mode: RoundingMode) -> Decimal:
    raw = nominal * rate * days / DAYS_IN_YEAR
    rounding = ROUND_HALF_UP if mode is RoundingMode.HALF_UP else ROUND_DOWN
    return raw.quantize(KOPECK, rounding=rounding)


def period_ends(spec: IssueSpec) -> list[date]:
    step = spec.coupon_frequency.months
    if step is None:
        return [spec.maturity_date]
    ends: list[date] = []
    k = 1
    while (end := add_months(spec.issue_date, k * step)) < spec.maturity_date:
        ends.append(end)
        k += 1
    ends.append(spec.maturity_date)
    return ends


def build_schedule(spec: IssueSpec, calendar: ProductionCalendar) -> Schedule:
    adjust = calendar.following if spec.business_day_rule is BusinessDayRule.FOLLOWING else calendar.preceding
    ends = period_ends(spec)
    periods: list[Period] = []
    start = spec.issue_date
    for number, end in enumerate(ends, start=1):
        days = (end - start).days
        periods.append(
            Period(
                number=number,
                start=start,
                end=end,
                days=days,
                coupon=coupon_amount(spec.nominal, spec.coupon_rate, days, spec.rounding_mode),
                principal=spec.nominal if end == spec.maturity_date else Decimal(0),
                payment_date=adjust(end),
            )
        )
        start = end
    return Schedule(periods=tuple(periods))


def simple_yield(spec: IssueSpec, schedule: Schedule) -> Decimal:
    income = schedule.total_payment - spec.price
    return (income / spec.price * DAYS_IN_YEAR / spec.term_days).quantize(Decimal("0.0001"))
