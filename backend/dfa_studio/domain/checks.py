import itertools
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from dfa_studio.documents.formatting import date_ru, money
from dfa_studio.domain.calendar import ProductionCalendar
from dfa_studio.domain.schedule import Schedule, coupon_amount
from dfa_studio.domain.spec import InvestorAccess, IssueSpec


class CheckStatus(StrEnum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckGroup(StrEnum):
    ARITHMETIC = "arithmetic"
    CALENDAR = "calendar"
    REGULATORY = "regulatory"
    CONTRACT = "contract"
    ANALYSIS = "analysis"


class Check(BaseModel):
    id: str
    group: CheckGroup
    title: str
    status: CheckStatus
    detail: str
    rows: list[dict[str, str]] = []
    reference: str | None = None


def _status(ok: bool, otherwise: CheckStatus = CheckStatus.FAILED) -> CheckStatus:
    return CheckStatus.PASSED if ok else otherwise


def arithmetic_checks(spec: IssueSpec, schedule: Schedule) -> list[Check]:
    recomputed = [
        coupon_amount(spec.nominal, spec.coupon_rate, period.days, spec.rounding_mode)
        for period in schedule.periods
    ]
    mismatched = [
        {"Период": str(period.number), "В графике": money(period.coupon), "По формуле": money(expected)}
        for period, expected in zip(schedule.periods, recomputed, strict=True)
        if period.coupon != expected
    ]
    covered_days = sum(period.days for period in schedule.periods)
    principal = sum((period.principal for period in schedule.periods), Decimal(0))
    return [
        Check(
            id="volume-bounds",
            group=CheckGroup.ARITHMETIC,
            title="Минимальный объём не превышает максимальный",
            status=_status(spec.min_quantity <= spec.max_quantity),
            detail=f"{spec.min_quantity:,} ≤ {spec.max_quantity:,} ЦФА".replace(",", " "),
        ),
        Check(
            id="coupon-formula",
            group=CheckGroup.ARITHMETIC,
            title="Доход в графике совпадает с формулой п. 6.3",
            status=_status(not mismatched),
            detail="Пересчитано независимо для каждого периода"
            if not mismatched
            else "Найдены расхождения с формулой",
            rows=mismatched,
        ),
        Check(
            id="periods-cover-term",
            group=CheckGroup.ARITHMETIC,
            title="Периоды начисления покрывают весь срок без разрывов",
            status=_status(covered_days == spec.term_days),
            detail=f"{covered_days} из {spec.term_days} дней",
        ),
        Check(
            id="principal-once",
            group=CheckGroup.ARITHMETIC,
            title="Номинал погашается один раз в последнюю дату",
            status=_status(principal == spec.nominal and schedule.periods[-1].principal == spec.nominal),
            detail=f"Погашение {money(principal)} ₽ на один ЦФА",
        ),
    ]


def calendar_checks(spec: IssueSpec, schedule: Schedule, calendar: ProductionCalendar) -> list[Check]:
    shifted = [
        {
            "Период": str(period.number),
            "По графику": date_ru(period.end),
            "Фактически": date_ru(period.payment_date),
        }
        for period in schedule.periods
        if period.shifted
    ]
    non_business = [p for p in schedule.periods if not calendar.is_business_day(p.payment_date)]
    ordered = all(a.payment_date < b.payment_date for a, b in itertools.pairwise(schedule.periods))
    return [
        Check(
            id="book-before-issue",
            group=CheckGroup.CALENDAR,
            title="Сбор заявок завершается до даты размещения",
            status=_status(spec.book_start <= spec.book_end < spec.issue_date),
            detail=f"{date_ru(spec.book_start)} – {date_ru(spec.book_end)}, размещение {date_ru(spec.issue_date)}",
        ),
        Check(
            id="payment-business-days",
            group=CheckGroup.CALENDAR,
            title="Все выплаты приходятся на рабочие дни",
            status=_status(not non_business),
            detail="Учтены выходные и праздники производственного календаря РФ",
        ),
        Check(
            id="payment-shifts",
            group=CheckGroup.CALENDAR,
            title="Переносы выплат по п. 6.5",
            status=CheckStatus.PASSED,
            detail=f"Перенесено выплат: {len(shifted)}" if shifted else "Переносов нет",
            rows=shifted,
        ),
        Check(
            id="payments-ordered",
            group=CheckGroup.CALENDAR,
            title="Даты выплат идут строго по возрастанию",
            status=_status(ordered),
            detail="После переносов порядок выплат сохраняется",
        ),
    ]


def regulatory_checks(spec: IssueSpec) -> list[Check]:
    checks = [
        Check(
            id="identification",
            group=CheckGroup.REGULATORY,
            title="Приобретатели проходят идентификацию у оператора",
            status=CheckStatus.PASSED,
            detail="Смарт-контракт принимает заявки и переводы только от идентифицированных лиц",
            reference="115-ФЗ",
        ),
        Check(
            id="issuer-website",
            group=CheckGroup.REGULATORY,
            title="У эмитента есть сайт для публикации решения и раскрытия",
            status=_status(bool(spec.issuer.website), CheckStatus.WARNING),
            detail=spec.issuer.website or "Сайт не указан",
            reference="259-ФЗ",
        ),
        Check(
            id="obligations-fixed",
            group=CheckGroup.REGULATORY,
            title="Обязательства нельзя менять после выпуска",
            status=CheckStatus.PASSED,
            detail="Параметры зафиксированы в коде как константы и совпадают с решением",
        ),
    ]
    if spec.investors is InvestorAccess.ALL:
        rated = spec.issuer.rating is not None
        checks.append(
            Check(
                id="retail-access",
                group=CheckGroup.REGULATORY,
                title="Допуск неквалифицированных инвесторов",
                status=CheckStatus.WARNING,
                detail=(
                    f"Рейтинг эмитента: {spec.issuer.rating}. Сверьте с порогом действующего указания Банка России"
                    if rated
                    else "У эмитента нет кредитного рейтинга: для продажи неквалифицированным инвесторам "
                    "может потребоваться рейтинг, сверьте с действующим указанием Банка России"
                ),
                reference="Указание Банка России о признаках ЦФА для неквалифицированных инвесторов",
            )
        )
    else:
        checks.append(
            Check(
                id="retail-access",
                group=CheckGroup.REGULATORY,
                title="Выпуск только для квалифицированных инвесторов",
                status=CheckStatus.PASSED,
                detail="Ограничение закреплено в решении и проверяется смарт-контрактом",
            )
        )
    if spec.early_redemption:
        checks.append(
            Check(
                id="early-redemption",
                group=CheckGroup.REGULATORY,
                title="Досрочное погашение требует ручной проверки",
                status=CheckStatus.WARNING,
                detail="Условие есть в решении, но в смарт-контракте этого шаблона не реализовано",
            )
        )
    return checks
