import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from dfa_studio.domain.fields import FieldValue, Origin
from dfa_studio.extraction.base import Extraction

NUMBER = r"\d{1,3}(?:[  ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?"
MULTIPLIER = r"млрд\.?|миллиард\w*|млн\.?|миллион\w*|тыс\.?|тысяч\w*"
CURRENCY = r"₽|руб\w*\.?|р\."
MONEY = rf"(?P<num>{NUMBER})\s*(?P<mult>{MULTIPLIER})?\s*(?P<cur>{CURRENCY})?"
SEP = r"\s*(?:—|–|-|:)?\s*"

MONTHS = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "ма": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}
MONTH_NAME = r"январ[ья]|феврал[ья]|марта?|апрел[ья]|ма[яй]|июн[ья]|июл[ья]|августа?|сентябр[ья]|октябр[ья]|ноябр[ья]|декабр[ья]"

WORD_NUMBERS = {
    "один": 1,
    "одного": 1,
    "два": 2,
    "двух": 2,
    "три": 3,
    "трёх": 3,
    "трех": 3,
    "четыре": 4,
    "шесть": 6,
    "девять": 9,
    "двенадцать": 12,
    "восемнадцать": 18,
}


def parse_number(raw: str) -> Decimal:
    return Decimal(raw.replace(" ", "").replace(" ", "").replace(",", "."))


def apply_multiplier(value: Decimal, multiplier: str | None) -> Decimal:
    if not multiplier:
        return value
    if multiplier.startswith(("млрд", "миллиард")):
        return value * 1_000_000_000
    if multiplier.startswith(("млн", "миллион")):
        return value * 1_000_000
    return value * 1_000


@dataclass
class _Context:
    text: str
    today: date
    values: dict[str, FieldValue] = field(default_factory=dict)
    consumed: list[tuple[int, int]] = field(default_factory=list)

    def free(self, match: re.Match[str]) -> bool:
        start, end = match.span()
        return all(end <= a or start >= b for a, b in self.consumed)

    def put(self, key: str, value: object, match: re.Match[str]) -> None:
        if key in self.values:
            return
        self.values[key] = FieldValue(value=value, origin=Origin.TEXT, evidence=match.group(0).strip())
        self.consumed.append(match.span())

    def search(self, pattern: str) -> re.Match[str] | None:
        for match in re.finditer(pattern, self.text, flags=re.IGNORECASE):
            if self.free(match):
                return match
        return None


def _money(match: re.Match[str]) -> Decimal:
    return apply_multiplier(parse_number(match.group("num")), match.group("mult"))


def _is_amount(match: re.Match[str]) -> bool:
    return bool(match.group("mult") or match.group("cur"))


def _inn(ctx: _Context) -> None:
    if match := ctx.search(r"ИНН\s*:?\s*(\d{12}|\d{10})"):
        ctx.put("issuer_inn", match.group(1), match)


def _nominal(ctx: _Context) -> None:
    if match := ctx.search(rf"номинал\w*{SEP}(?:в\s+|по\s+)?{MONEY}"):
        ctx.put("nominal", _money(match), match)


def _price(ctx: _Context) -> None:
    if match := ctx.search(rf"(?:цен\w*\s+размещени\w*|по\s+цене){SEP}{MONEY}"):
        ctx.put("price", _money(match), match)


def _min_amount(ctx: _Context) -> None:
    share = ctx.search(
        r"(?:минимальн\w*\s+объ[её]м\w*|не\s+менее|минимум|состоится\s+от)"
        r"\s*(?:—|–|-|:)?\s*(?P<pct>\d+(?:[.,]\d+)?)\s*%\s*(?:от\s+)?(?:объ[её]м\w*|максимум\w*|максимальн\w*)?"
    )
    if share:
        ctx.values["_min_share"] = FieldValue(
            value=parse_number(share.group("pct")) / 100, origin=Origin.TEXT, evidence=share.group(0).strip()
        )
        ctx.consumed.append(share.span())
        return
    pattern = (
        rf"(?:минимальн\w*\s+объ[её]м\w*|не\s+менее|минимум|состоится\s+от|хотя\s+бы){SEP}(?:в\s+)?{MONEY}"
    )
    match = ctx.search(pattern)
    if match and _is_amount(match):
        ctx.put("min_amount", _money(match), match)


def _max_amount(ctx: _Context) -> None:
    pattern = (
        r"(?:привлечь|привлечение|разместить|объ[её]м\w*(?:\s+выпуска)?|максимум|максимальн\w*\s+объ[её]м\w*|"
        rf"на\s+сумму|выпуск\w*\s+на){SEP}(?:до\s+|не\s+более\s+)?{MONEY}"
    )
    match = ctx.search(pattern)
    if match and _is_amount(match):
        ctx.put("max_amount", _money(match), match)
        return
    for candidate in re.finditer(rf"(?:до\s+)?{MONEY}", ctx.text, flags=re.IGNORECASE):
        if ctx.free(candidate) and candidate.group("mult") and _money(candidate) >= 1_000_000:
            ctx.put("max_amount", _money(candidate), candidate)
            return


FREQUENCIES: list[tuple[str, str]] = [
    (r"ежемесячн\w*|раз\s+в\s+месяц|каждый\s+месяц|помесячн\w*", "monthly"),
    (r"ежеквартальн\w*|раз\s+в\s+квартал|каждый\s+квартал|поквартальн\w*", "quarterly"),
    (
        r"раз\s+в\s+полгода|раз\s+в\s+пол\s*года|полугодов\w*|каждые\s+полгода|два\s+раза\s+в\s+год",
        "semiannual",
    ),
    (r"раз\s+в\s+год|ежегодн\w*|каждый\s+год", "annual"),
    (
        r"(?:в\s+конце\s+срока|при\s+погашении|в\s+дату\s+погашения|вместе\s+с\s+номиналом|"
        r"одним\s+платеж\w*|разово\s+в\s+конце)",
        "at_maturity",
    ),
]


def _frequency(ctx: _Context) -> None:
    for pattern, value in FREQUENCIES:
        if match := ctx.search(pattern):
            ctx.put("coupon_frequency", value, match)
            return


def _rate(ctx: _Context) -> None:
    match = ctx.search(r"(?P<num>\d+(?:[.,]\d+)?)\s*(?:%|процент\w*)(?:\s*годовых)?")
    if match is None:
        match = ctx.search(
            r"(?:ставк\w*|купон\w*|доходност\w*)\s*(?:—|-|:|в)?\s*(?P<num>\d+(?:[.,]\d+)?)(?!\s*\d)"
        )
    if match:
        ctx.put("coupon_rate", parse_number(match.group("num")), match)


def _term(ctx: _Context) -> None:
    words = "|".join(WORD_NUMBERS)
    pattern = (
        r"(?:на\s+срок|сроком|срок\w*(?:\s+обращени\w*)?|на)\s+(?:в\s+)?"
        rf"(?P<n>\d+|{words}|полгода|полтора\s+года|год)\s*(?P<unit>месяц\w*|мес\.?|год\w*|лет)?"
    )
    for match in re.finditer(pattern, ctx.text, flags=re.IGNORECASE):
        if not ctx.free(match):
            continue
        n, unit = match.group("n").lower(), (match.group("unit") or "").lower()
        if n == "полгода":
            months = 6
        elif n.startswith("полтора"):
            months = 18
        elif n == "год":
            months = 12
        else:
            count = int(n) if n.isdigit() else WORD_NUMBERS[n]
            if unit.startswith(("год", "лет")):
                months = count * 12
            elif unit.startswith("мес"):
                months = count
            else:
                continue
        ctx.put("term_months", months, match)
        return


def _issue_date(ctx: _Context) -> None:
    numeric = r"(?P<d>\d{1,2})\.(?P<m>\d{1,2})\.(?P<y>\d{4})"
    verbal = rf"(?P<vd>\d{{1,2}})\s+(?P<vm>{MONTH_NAME})(?:\s+(?P<vy>\d{{4}}))?(?:\s*г(?:ода|\.)?)?"
    match = ctx.search(rf"(?:{numeric}|{verbal})")
    if not match:
        return
    if match.group("d"):
        day = date(int(match.group("y")), int(match.group("m")), int(match.group("d")))
    else:
        month_word = match.group("vm").lower()
        month = next(number for stem, number in MONTHS.items() if month_word.startswith(stem))
        year = int(match.group("vy")) if match.group("vy") else ctx.today.year
        day = date(year, month, int(match.group("vd")))
        if not match.group("vy") and day < ctx.today:
            day = date(year + 1, month, day.day)
    ctx.put("issue_date", day, match)


def _investors(ctx: _Context) -> None:
    if match := ctx.search(
        r"неквал\w*|всем\s+инвестор\w*|для\s+всех|розничн\w*|физическ\w*\s+лиц\w*|физлиц\w*|частн\w*\s+инвестор\w*"
    ):
        ctx.put("investors", "all", match)
    elif match := ctx.search(r"квал\w*(?:\s+инвестор\w*)?"):
        ctx.put("investors", "qualified_only", match)


def _business_day(ctx: _Context) -> None:
    if match := ctx.search(r"(?:следующ\w*|ближайш\w*\s+следующ\w*)\s+рабоч\w*\s+д\w*"):
        ctx.put("business_day_rule", "following", match)
    elif match := ctx.search(r"(?:предыдущ\w*|предшествующ\w*)\s+рабоч\w*\s+д\w*"):
        ctx.put("business_day_rule", "preceding", match)


def _rounding(ctx: _Context) -> None:
    if match := ctx.search(r"математическ\w*\s+округл\w*|округл\w*\s+(?:по\s+правилам\s+)?математ\w*"):
        ctx.put("rounding_mode", "half_up", match)
    elif match := ctx.search(
        r"округл\w*\s+вниз|отбрасыва\w*\s+(?:дол\w*\s+)?копе\w*|без\s+округления\s+вверх"
    ):
        ctx.put("rounding_mode", "down", match)


def _early_redemption(ctx: _Context) -> None:
    if match := ctx.search(
        r"(?:без|не\s+предусм\w*|нет)\s+(?:права\s+|возможности\s+)?досрочн\w*(?:\s+погашени\w*)?"
    ):
        ctx.put("early_redemption", False, match)
    elif match := ctx.search(r"(?:с\s+)?(?:правом|возможностью|опцией)?\s*досрочн\w*\s+погашени\w*"):
        ctx.put("early_redemption", True, match)


def _allocation(ctx: _Context) -> None:
    if match := ctx.search(r"пропорциональн\w*"):
        ctx.put("allocation", "pro_rata", match)
    elif match := ctx.search(r"в\s+порядке\s+очеред\w*|кто\s+первый|по\s+очереди"):
        ctx.put("allocation", "first_come", match)


def _book_days(ctx: _Context) -> None:
    pattern = r"(?:сбор\w*\s+заявок|заявки\s+собира\w*|книг\w*\s+заявок)\s*(?:—|-|:|в\s+течение)?\s*(?P<n>\d+)\s*(?:рабоч\w*\s+)?дн"
    if match := ctx.search(pattern):
        ctx.put("book_days", int(match.group("n")), match)


STEPS: list[Callable[[_Context], None]] = [
    _inn,
    _frequency,
    _business_day,
    _rounding,
    _early_redemption,
    _book_days,
    _nominal,
    _price,
    _min_amount,
    _max_amount,
    _rate,
    _term,
    _issue_date,
    _investors,
    _allocation,
]


class RuleExtractor:
    name = "rules"

    def __init__(self, today: date | None = None) -> None:
        self._today = today

    def extract(self, text: str) -> Extraction:
        ctx = _Context(text=text, today=self._today or date.today())
        for step in STEPS:
            step(ctx)
        share = ctx.values.pop("_min_share", None)
        if share and "max_amount" in ctx.values and "min_amount" not in ctx.values:
            maximum = Decimal(ctx.values["max_amount"].value)
            ctx.values["min_amount"] = FieldValue(
                value=(maximum * share.value).quantize(Decimal(1)),
                origin=Origin.TEXT,
                evidence=share.evidence,
            )
        return Extraction(provider=self.name, values=ctx.values)
