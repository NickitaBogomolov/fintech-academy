from datetime import date, time

from dfa_studio.contracts.generator import ContractFault, generate_contract, kopecks, timestamp
from dfa_studio.domain.schedule import build_schedule


def test_timestamps_are_moscow_time() -> None:
    assert timestamp(date(2026, 12, 15)) == 1_797_282_000
    assert timestamp(date(2026, 12, 8), time(9, 0)) - timestamp(date(2026, 12, 8)) == 9 * 3600


def test_contract_constants_follow_specification(spec, calendar) -> None:
    schedule = build_schedule(spec, calendar)
    contract = generate_contract(spec, schedule)
    assert "uint256 public constant NOMINAL = 100_000;" in contract.source
    assert "uint256 public constant MAX_QUANTITY = 300_000;" in contract.source
    assert "bool public constant QUALIFIED_ONLY = true;" in contract.source
    assert [period.coupon for period in contract.periods] == [1529, 1529, 1381, 1529, 1479, 1529]
    assert contract.periods[4].payment_date == timestamp(date(2027, 5, 17))


def test_faults_change_only_targeted_values(spec, calendar) -> None:
    schedule = build_schedule(spec, calendar)
    clean = generate_contract(spec, schedule)
    rounded = generate_contract(spec, schedule, ContractFault.ROUNDING_DOWN)
    early = generate_contract(spec, schedule, ContractFault.EARLY_PAYMENT)
    unbounded = generate_contract(spec, schedule, ContractFault.NO_MINIMUM)
    assert [p.coupon for p in rounded.periods] == [1528, 1528, 1380, 1528, 1479, 1528]
    assert early.periods[0].payment_date == clean.periods[0].payment_date - 86_400
    assert early.periods[1:] == clean.periods[1:]
    assert unbounded.parameters["min_quantity"] == 0
    assert kopecks(spec.nominal) == 100_000
