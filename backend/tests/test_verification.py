import pytest

from dfa_studio.contracts.generator import ContractFault, generate_contract
from dfa_studio.domain.checks import CheckStatus, arithmetic_checks, calendar_checks, regulatory_checks
from dfa_studio.domain.schedule import build_schedule
from dfa_studio.domain.spec import InvestorAccess
from dfa_studio.settings import get_settings
from dfa_studio.verification.pipeline import ContractVerifier
from dfa_studio.verification.slither import SlitherRunner, summarize
from dfa_studio.verification.solc import SolidityCompiler

settings = get_settings()
compiler = SolidityCompiler(settings.solc_dir)
requires_solc = pytest.mark.skipif(not compiler.available, reason="solc toolchain is not installed")


@pytest.fixture
def verifier() -> ContractVerifier:
    return ContractVerifier(compiler, SlitherRunner(settings.solc_dir / "solc", enabled=False))


def statuses(checks) -> dict[str, CheckStatus]:
    return {check.id: check.status for check in checks}


def test_document_checks_pass_for_consistent_spec(spec, calendar) -> None:
    schedule = build_schedule(spec, calendar)
    checks = [
        *arithmetic_checks(spec, schedule),
        *calendar_checks(spec, schedule, calendar),
        *regulatory_checks(spec),
    ]
    assert all(check.status is CheckStatus.PASSED for check in checks)
    shifts = next(check for check in checks if check.id == "payment-shifts")
    assert shifts.rows == [{"Период": "5", "По графику": "15.05.2027", "Фактически": "17.05.2027"}]


def test_retail_issue_without_rating_gets_warning(spec) -> None:
    retail = spec.model_copy(update={"investors": InvestorAccess.ALL})
    check = next(check for check in regulatory_checks(retail) if check.id == "retail-access")
    assert check.status is CheckStatus.WARNING


@requires_solc
def test_generated_contract_behaves_as_documented(spec, calendar, verifier) -> None:
    schedule = build_schedule(spec, calendar)
    result = verifier.verify(spec, schedule, generate_contract(spec, schedule), static_analysis=False)
    assert set(statuses(result.checks).values()) == {CheckStatus.PASSED}
    assert len(result.checks) == 11


@requires_solc
@pytest.mark.parametrize(
    ("fault", "failing"),
    [
        (ContractFault.ROUNDING_DOWN, {"payments-match-document"}),
        (ContractFault.EARLY_PAYMENT, {"no-early-payments"}),
        (ContractFault.NO_MINIMUM, {"refund"}),
    ],
)
def test_injected_faults_are_detected(spec, calendar, verifier, fault, failing) -> None:
    schedule = build_schedule(spec, calendar)
    result = verifier.verify(spec, schedule, generate_contract(spec, schedule, fault), static_analysis=False)
    failed = {
        check_id for check_id, status in statuses(result.checks).items() if status is CheckStatus.FAILED
    }
    assert failed == failing


def test_slither_summary_classifies_severity() -> None:
    low = summarize([{"impact": "Low", "check": "calls-loop", "description": "x"}])
    high = summarize([{"impact": "High", "check": "reentrancy-eth", "description": "x"}])
    clean = summarize([{"impact": "Informational", "check": "naming-convention", "description": "x"}])
    assert (low.status, high.status, clean.status) == (
        CheckStatus.WARNING,
        CheckStatus.FAILED,
        CheckStatus.PASSED,
    )
