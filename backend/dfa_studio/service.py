import difflib
import statistics
import uuid
from collections import Counter
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel

from dfa_studio.benchmark import benchmark_today, run_benchmark
from dfa_studio.contracts.generator import FAULT_LABELS, ContractFault, generate_contract
from dfa_studio.documents.render import Operator, TemplateStore, render_document
from dfa_studio.domain.builder import SpecError, build_spec
from dfa_studio.domain.calendar import ProductionCalendar
from dfa_studio.domain.checks import (
    Check,
    CheckStatus,
    arithmetic_checks,
    calendar_checks,
    regulatory_checks,
)
from dfa_studio.domain.fields import FIELDS, FieldValue, Origin
from dfa_studio.domain.schedule import Schedule, build_schedule, simple_yield
from dfa_studio.domain.spec import IssueSpec
from dfa_studio.extraction.drafting import Draft, build_draft, make_extractor
from dfa_studio.extraction.rules import RuleExtractor
from dfa_studio.registry import find_issuer
from dfa_studio.settings import Settings
from dfa_studio.storage import Storage
from dfa_studio.verification.pipeline import ContractVerifier
from dfa_studio.verification.slither import SlitherRunner
from dfa_studio.verification.solc import SolidityCompiler

DEFAULT_TEMPLATE = "decision_coupon"
SAMPLE_VALUES: dict[str, Any] = {
    "issuer_inn": "0000000001",
    "nominal": "1000",
    "max_amount": "300000000",
    "min_amount": "100000000",
    "issue_date": "2026-12-15",
    "term_months": 6,
    "coupon_rate": "18",
    "coupon_frequency": "monthly",
    "rounding_mode": "half_up",
    "business_day_rule": "following",
    "early_redemption": False,
    "investors": "qualified_only",
}


class IssueRequest(BaseModel):
    text: str
    values: dict[str, FieldValue]
    template_id: str = DEFAULT_TEMPLATE
    started_at: datetime | None = None
    questions_asked: int = 0


class PeriodView(BaseModel):
    number: int
    start: date
    end: date
    days: int
    coupon: Decimal
    principal: Decimal
    payment: Decimal
    payment_date: date
    shifted: bool


def _periods(schedule: Schedule) -> list[PeriodView]:
    return [
        PeriodView(
            number=p.number,
            start=p.start,
            end=p.end,
            days=p.days,
            coupon=p.coupon,
            principal=p.principal,
            payment=p.payment,
            payment_date=p.payment_date,
            shifted=p.shifted,
        )
        for p in schedule.periods
    ]


def summarize_checks(checks: list[Check]) -> dict[str, int]:
    counts = Counter(check.status.value for check in checks)
    return {status.value: counts.get(status.value, 0) for status in CheckStatus}


class Studio:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.calendar = ProductionCalendar()
        self.storage = Storage(settings.database_path)
        self.templates = TemplateStore(settings.data_dir / "templates")
        self.extractor = make_extractor(settings)
        self.compiler = SolidityCompiler(settings.solc_dir)
        self.slither = SlitherRunner(settings.solc_dir / "solc", settings.slither_enabled)
        self.verifier = ContractVerifier(self.compiler, self.slither)
        self.operator = Operator(
            name=settings.operator_name, ogrn=settings.operator_ogrn, website=settings.operator_website
        )

    @property
    def provider_label(self) -> str:
        return (
            self.settings.llm_label
            if self.settings.llm_provider == "openai"
            else "Правила, без внешних вызовов"
        )

    def draft(self, text: str, inn: str | None, answers: dict[str, Any] | None = None) -> Draft:
        extraction = self.extractor.extract(text)
        return build_draft(extraction, self.calendar, date.today(), inn=inn, answers=answers)

    def _spec(self, values: dict[str, FieldValue]) -> IssueSpec:
        raw = {key: item.value for key, item in values.items()}
        inn = str(raw.get("issuer_inn") or "")
        issuer = find_issuer(inn)
        if issuer is None:
            raise SpecError({"issuer_inn": "эмитент не найден в реестре"})
        issue_date = raw.get("issue_date")
        year = date.fromisoformat(str(issue_date)).year if issue_date else date.today().year
        number = self.storage.next_issue_number(issuer.code, year)
        return build_spec(raw, issuer, number, self.calendar)

    def _document_checks(self, spec: IssueSpec, schedule: Schedule) -> list[Check]:
        return [
            *arithmetic_checks(spec, schedule),
            *calendar_checks(spec, schedule, self.calendar),
            *regulatory_checks(spec),
        ]

    def create_issue(self, request: IssueRequest) -> dict[str, Any]:
        spec = self._spec(request.values)
        schedule = build_schedule(spec, self.calendar)
        template = self.templates.get(request.template_id)
        document = render_document(template.source, spec, schedule, self.operator, date.today())
        contract = generate_contract(spec, schedule)
        verification = self.verifier.verify(spec, schedule, contract)
        checks = [*self._document_checks(spec, schedule), *verification.checks]

        created_at = datetime.now(UTC)
        preparation = None
        if request.started_at:
            preparation = max(0.0, (created_at - request.started_at.astimezone(UTC)).total_seconds())
        origins = Counter(item.origin.value for item in request.values.values())
        summary = summarize_checks(checks)
        issue_id = uuid.uuid4().hex[:12]
        package = {
            "id": issue_id,
            "created_at": created_at.isoformat(),
            "text": request.text,
            "provider": self.provider_label,
            "template": {"id": template.id, "title": template.title},
            "spec": spec.model_dump(mode="json"),
            "values": {key: item.model_dump(mode="json") for key, item in request.values.items()},
            "schedule": [period.model_dump(mode="json") for period in _periods(schedule)],
            "totals": {
                "coupon": str(schedule.total_coupon),
                "payment": str(schedule.total_payment),
                "simple_yield": str(simple_yield(spec, schedule)),
            },
            "document": document,
            "contract": {"name": contract.name, "source": contract.source},
            "compiler": verification.compiler_version,
            "checks": [check.model_dump(mode="json") for check in checks],
            "summary": summary,
            "fault_runs": [],
            "metrics": {
                "preparation_seconds": preparation,
                "fields_total": len(FIELDS),
                "from_text": origins.get(Origin.TEXT.value, 0),
                "from_answers": origins.get(Origin.ANSWER.value, 0),
                "from_defaults": origins.get(Origin.DEFAULT.value, 0),
                "questions_asked": request.questions_asked,
            },
        }
        self.storage.save_issue(issue_id, spec.issue_number, spec.issuer.code, package)
        return package

    def get_issue(self, issue_id: str) -> dict[str, Any]:
        package = self.storage.get_issue(issue_id)
        if package is None:
            raise KeyError(issue_id)
        return package

    def list_issues(self) -> list[dict[str, Any]]:
        return [
            {
                "id": item["id"],
                "created_at": item["created_at"],
                "issue_number": item["spec"]["issue_number"],
                "issuer": item["spec"]["issuer"]["short_name"],
                "max_amount": item["spec"]["max_amount"],
                "coupon_rate": item["spec"]["coupon_rate"],
                "maturity_date": item["spec"]["maturity_date"],
                "summary": item["summary"],
                "preparation_seconds": item["metrics"]["preparation_seconds"],
            }
            for item in self.storage.list_issues()
        ]

    def run_fault(self, issue_id: str, fault: ContractFault) -> dict[str, Any]:
        package = self.get_issue(issue_id)
        spec = IssueSpec.model_validate(package["spec"])
        schedule = build_schedule(spec, self.calendar)
        clean = generate_contract(spec, schedule)
        broken = generate_contract(spec, schedule, fault)
        verification = self.verifier.verify(spec, schedule, broken, static_analysis=False)
        failed = [check for check in verification.checks if check.status is CheckStatus.FAILED]
        diff = [
            line
            for line in difflib.unified_diff(
                clean.source.splitlines(), broken.source.splitlines(), lineterm="", n=0
            )
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        ]
        record = {
            "fault": fault.value,
            "label": FAULT_LABELS[fault],
            "caught": bool(failed),
            "failed_checks": [check.title for check in failed],
            "created_at": datetime.now(UTC).isoformat(),
        }
        package["fault_runs"].append(record)
        self.storage.save_issue(issue_id, spec.issue_number, spec.issuer.code, package)
        return {
            **record,
            "diff": diff,
            "checks": [check.model_dump(mode="json") for check in verification.checks],
        }

    def metrics(self) -> dict[str, Any]:
        issues = self.storage.list_issues()
        durations = [
            item["metrics"]["preparation_seconds"]
            for item in issues
            if item["metrics"]["preparation_seconds"] is not None
        ]
        fields = Counter()
        for item in issues:
            for key in ("fields_total", "from_text", "from_answers", "from_defaults", "questions_asked"):
                fields[key] += item["metrics"][key]
        checks = Counter()
        for item in issues:
            checks.update(item["summary"])
        fault_runs = [run for item in issues for run in item.get("fault_runs", [])]
        return {
            "issues": len(issues),
            "median_preparation_seconds": statistics.median(durations) if durations else None,
            "fields": dict(fields),
            "avg_questions": round(fields["questions_asked"] / len(issues), 1) if issues else None,
            "checks": dict(checks),
            "fault_runs": len(fault_runs),
            "faults_caught": sum(1 for run in fault_runs if run["caught"]),
            "timeline": [
                {
                    "created_at": item["created_at"],
                    "issue_number": item["spec"]["issue_number"],
                    "preparation_seconds": item["metrics"]["preparation_seconds"],
                    "questions_asked": item["metrics"]["questions_asked"],
                }
                for item in reversed(issues)
            ],
            "benchmark": self.storage.latest_benchmark(),
        }

    def run_benchmark(self) -> dict[str, Any]:
        extractor = self.extractor
        if isinstance(extractor, RuleExtractor):
            extractor = RuleExtractor(today=benchmark_today())
        result = run_benchmark(extractor, self.provider_label)
        self.storage.save_benchmark(result)
        return result

    def system(self) -> dict[str, Any]:
        external = []
        if self.settings.llm_provider == "openai":
            external.append(urlparse(self.settings.llm_base_url).netloc)
        return {
            "llm": {
                "provider": self.settings.llm_provider,
                "label": self.provider_label,
                "model": self.settings.llm_model if self.settings.llm_provider == "openai" else None,
                "endpoint": external[0] if external else None,
            },
            "toolchain": {
                "solc": self.compiler.version() if self.compiler.available else None,
                "slither": self.slither.available,
                "evm": "py-evm внутри процесса",
            },
            "storage": "SQLite в каталоге данных сервиса",
            "external_hosts": external,
            "operator": {"name": self.operator.name, "website": self.operator.website},
        }

    def sample_document(self, source: str) -> str:
        issuer = find_issuer(SAMPLE_VALUES["issuer_inn"])
        if issuer is None:
            raise KeyError(SAMPLE_VALUES["issuer_inn"])
        spec = build_spec(SAMPLE_VALUES, issuer, f"{issuer.code}-000-2026", self.calendar)
        return render_document(source, spec, build_schedule(spec, self.calendar), self.operator, date.today())
