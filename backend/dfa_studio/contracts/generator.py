from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_DOWN, Decimal
from enum import StrEnum
from importlib import resources

from jinja2 import Environment, StrictUndefined

from dfa_studio.domain.schedule import DAYS_IN_YEAR, KOPECK, Schedule
from dfa_studio.domain.spec import InvestorAccess, IssueSpec

MOSCOW = timezone(timedelta(hours=3))
CONTRACT_NAME = "DigitalFinancialAsset"
TOKEN_NAME = "SettlementToken"


class ContractFault(StrEnum):
    ROUNDING_DOWN = "rounding_down"
    EARLY_PAYMENT = "early_payment"
    NO_MINIMUM = "no_minimum"


FAULT_LABELS = {
    ContractFault.ROUNDING_DOWN: "В коде доход округляется вниз, а в решении о выпуске — математически",
    ContractFault.EARLY_PAYMENT: "В коде дата первой выплаты на день раньше, чем в графике",
    ContractFault.NO_MINIMUM: "В коде не задан минимальный объём выпуска",
}


@dataclass(frozen=True)
class ContractPeriod:
    payment_date: int
    coupon: int


@dataclass(frozen=True)
class GeneratedContract:
    name: str
    source: str
    periods: list[ContractPeriod]
    parameters: dict[str, int | str | bool] = field(default_factory=dict)
    fault: ContractFault | None = None


def timestamp(day: date, at: time = time(0, 0)) -> int:
    return int(datetime.combine(day, at, tzinfo=MOSCOW).timestamp())


def kopecks(amount: Decimal) -> int:
    return int((amount / KOPECK).to_integral_value())


def _template(name: str) -> str:
    return resources.files("dfa_studio.contracts").joinpath("templates", name).read_text(encoding="utf-8")


def token_source() -> str:
    return _template(f"{TOKEN_NAME}.sol")


def _periods(spec: IssueSpec, schedule: Schedule, fault: ContractFault | None) -> list[ContractPeriod]:
    periods = []
    for index, period in enumerate(schedule.periods):
        coupon = period.coupon
        if fault is ContractFault.ROUNDING_DOWN:
            raw = spec.nominal * spec.coupon_rate * period.days / DAYS_IN_YEAR
            coupon = raw.quantize(KOPECK, rounding=ROUND_DOWN)
        payment_day = period.payment_date
        if fault is ContractFault.EARLY_PAYMENT and index == 0:
            payment_day -= timedelta(days=1)
        periods.append(ContractPeriod(payment_date=timestamp(payment_day), coupon=kopecks(coupon)))
    return periods


def generate_contract(
    spec: IssueSpec, schedule: Schedule, fault: ContractFault | None = None
) -> GeneratedContract:
    periods = _periods(spec, schedule, fault)
    parameters: dict[str, int | str | bool] = {
        "issue_number": spec.issue_number,
        "issuer_name": spec.issuer.short_name,
        "nominal": kopecks(spec.nominal),
        "price": kopecks(spec.price),
        "min_quantity": 0 if fault is ContractFault.NO_MINIMUM else spec.min_quantity,
        "max_quantity": spec.max_quantity,
        "book_start": timestamp(spec.book_start, time(9, 0)),
        "book_end": timestamp(spec.book_end, time(18, 0)),
        "issue_date": timestamp(spec.issue_date),
        "qualified_only": spec.investors is InvestorAccess.QUALIFIED_ONLY,
    }
    env = Environment(undefined=StrictUndefined, keep_trailing_newline=True, autoescape=False)
    env.filters["sol_int"] = lambda value: f"{value:_}"
    source = env.from_string(_template(f"{CONTRACT_NAME}.sol.j2")).render(**parameters, periods=periods)
    return GeneratedContract(
        name=CONTRACT_NAME, source=source, periods=periods, parameters=parameters, fault=fault
    )
