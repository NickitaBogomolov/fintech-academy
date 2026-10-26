from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class FieldKind(StrEnum):
    MONEY = "money"
    PERCENT = "percent"
    INTEGER = "integer"
    DATE = "date"
    CHOICE = "choice"
    BOOLEAN = "boolean"
    TEXT = "text"


class Origin(StrEnum):
    TEXT = "text"
    ANSWER = "answer"
    DEFAULT = "default"
    REGISTRY = "registry"


class Choice(BaseModel):
    value: Any
    label: str


class FieldDef(BaseModel):
    key: str
    label: str
    group: str
    kind: FieldKind
    question: str
    hint: str | None = None
    choices: list[Choice] = []
    default: Any = None


class FieldValue(BaseModel):
    value: Any
    origin: Origin
    evidence: str | None = None


GROUPS = ["Эмитент", "Размещение", "Доходность", "Погашение", "Инвесторы"]

FIELDS: list[FieldDef] = [
    FieldDef(
        key="issuer_inn",
        label="ИНН эмитента",
        group="Эмитент",
        kind=FieldKind.TEXT,
        question="Укажите ИНН эмитента",
        hint="Наименование, ОГРН, адрес и руководитель подтянутся из реестра",
    ),
    FieldDef(
        key="nominal",
        label="Номинал одного ЦФА",
        group="Размещение",
        kind=FieldKind.MONEY,
        question="Какой номинал у одного ЦФА?",
        choices=[
            Choice(value="1000", label="1 000 ₽"),
            Choice(value="10000", label="10 000 ₽"),
            Choice(value="100000", label="100 000 ₽"),
        ],
    ),
    FieldDef(
        key="price",
        label="Цена размещения",
        group="Размещение",
        kind=FieldKind.MONEY,
        question="По какой цене размещается один ЦФА?",
        hint="По умолчанию равна номиналу",
    ),
    FieldDef(
        key="max_amount",
        label="Максимальный объём выпуска",
        group="Размещение",
        kind=FieldKind.MONEY,
        question="Сколько нужно привлечь максимум?",
    ),
    FieldDef(
        key="min_amount",
        label="Минимальный объём выпуска",
        group="Размещение",
        kind=FieldKind.MONEY,
        question="При каком минимальном объёме выпуск считается состоявшимся?",
        hint="Если заявок окажется меньше, деньги вернутся инвесторам",
    ),
    FieldDef(
        key="issue_date",
        label="Дата размещения",
        group="Размещение",
        kind=FieldKind.DATE,
        question="Когда планируется размещение?",
        hint="Сбор заявок закончится в предыдущий рабочий день",
    ),
    FieldDef(
        key="book_days",
        label="Сбор заявок, рабочих дней",
        group="Размещение",
        kind=FieldKind.INTEGER,
        question="Сколько рабочих дней собирать заявки?",
        default=5,
    ),
    FieldDef(
        key="allocation",
        label="Удовлетворение заявок при переподписке",
        group="Размещение",
        kind=FieldKind.CHOICE,
        question="Как распределять ЦФА, если заявок больше объёма?",
        choices=[
            Choice(value="first_come", label="В порядке очереди"),
            Choice(value="pro_rata", label="Пропорционально"),
        ],
        default="first_come",
    ),
    FieldDef(
        key="coupon_rate",
        label="Ставка дохода, % годовых",
        group="Доходность",
        kind=FieldKind.PERCENT,
        question="Какая ставка дохода, % годовых?",
    ),
    FieldDef(
        key="coupon_frequency",
        label="Периодичность выплат",
        group="Доходность",
        kind=FieldKind.CHOICE,
        question="Как часто выплачивать доход?",
        choices=[
            Choice(value="monthly", label="Ежемесячно"),
            Choice(value="quarterly", label="Ежеквартально"),
            Choice(value="semiannual", label="Раз в полгода"),
            Choice(value="annual", label="Раз в год"),
            Choice(value="at_maturity", label="В дату погашения"),
        ],
    ),
    FieldDef(
        key="rounding_mode",
        label="Округление выплат",
        group="Доходность",
        kind=FieldKind.CHOICE,
        question="Как округлять доход на один ЦФА до копеек?",
        hint="Частый источник расхождений между документом и кодом",
        choices=[
            Choice(value="half_up", label="Математически"),
            Choice(value="down", label="Отбрасывать доли копейки"),
        ],
    ),
    FieldDef(
        key="term_months",
        label="Срок обращения, месяцев",
        group="Погашение",
        kind=FieldKind.INTEGER,
        question="На какой срок выпуск?",
        choices=[
            Choice(value=3, label="3 месяца"),
            Choice(value=6, label="6 месяцев"),
            Choice(value=12, label="1 год"),
        ],
    ),
    FieldDef(
        key="business_day_rule",
        label="Перенос выплат с выходных",
        group="Погашение",
        kind=FieldKind.CHOICE,
        question="Если дата выплаты выпала на выходной, куда её переносить?",
        choices=[
            Choice(value="following", label="На следующий рабочий день"),
            Choice(value="preceding", label="На предыдущий рабочий день"),
        ],
    ),
    FieldDef(
        key="early_redemption",
        label="Досрочное погашение по инициативе эмитента",
        group="Погашение",
        kind=FieldKind.BOOLEAN,
        question="Может ли эмитент погасить выпуск досрочно?",
        choices=[Choice(value=False, label="Нет"), Choice(value=True, label="Да")],
    ),
    FieldDef(
        key="investors",
        label="Круг инвесторов",
        group="Инвесторы",
        kind=FieldKind.CHOICE,
        question="Кому можно предлагать выпуск?",
        hint="Влияет на допуск неквалифицированных инвесторов по правилам Банка России",
        choices=[
            Choice(value="qualified_only", label="Только квалифицированным"),
            Choice(value="all", label="Всем инвесторам"),
        ],
    ),
]

FIELDS_BY_KEY = {field.key: field for field in FIELDS}


def coerce(field: FieldDef, raw: Any) -> Any:
    if raw is None or raw == "":
        return None
    match field.kind:
        case FieldKind.MONEY | FieldKind.PERCENT:
            return Decimal(str(raw).replace(" ", "").replace(",", "."))
        case FieldKind.INTEGER:
            return int(raw)
        case FieldKind.DATE:
            return raw if isinstance(raw, date) else date.fromisoformat(str(raw))
        case FieldKind.BOOLEAN:
            return raw if isinstance(raw, bool) else str(raw).lower() in {"true", "1", "да"}
        case _:
            return str(raw).strip()


def serialize(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, date):
        return value.isoformat()
    return value
