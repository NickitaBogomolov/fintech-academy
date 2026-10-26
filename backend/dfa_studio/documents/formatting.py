from datetime import date
from decimal import Decimal

from num2words import num2words

MONTHS_GENITIVE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

FREQUENCY_LABELS = {
    "monthly": "ежемесячно",
    "quarterly": "ежеквартально",
    "semiannual": "раз в полгода",
    "annual": "раз в год",
    "at_maturity": "в дату погашения",
}


def plural(value: int, forms: tuple[str, str, str]) -> str:
    tail = value % 100
    if 11 <= tail <= 14:
        return forms[2]
    if value % 10 == 1:
        return forms[0]
    if 2 <= value % 10 <= 4:
        return forms[1]
    return forms[2]


def group_digits(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def money(value: Decimal) -> str:
    rubles = int(value)
    kopecks = int((value - rubles) * 100)
    return f"{group_digits(rubles)},{kopecks:02d}"


def money_short(value: Decimal) -> str:
    if value == int(value):
        return group_digits(int(value))
    return money(value)


def int_words(value: int) -> str:
    return f"{group_digits(value)} ({num2words(value, lang='ru')})"


def money_words(value: Decimal) -> str:
    rubles = int(value)
    kopecks = int((value - rubles) * 100)
    words = f"{money_short(value)} ({num2words(rubles, lang='ru')}) российских рублей"
    if kopecks:
        words += f" {kopecks:02d} копеек"
    return words


def percent(value: Decimal) -> str:
    return f"{value * 100:.2f}".replace(".", ",") + "%"


def percent_words(value: Decimal) -> str:
    number = (value * 100).normalize()
    spoken = (
        num2words(int(number), lang="ru") if number == int(number) else num2words(float(number), lang="ru")
    )
    noun = plural(int(number), ("процент", "процента", "процентов")) if number == int(number) else "процента"
    return f"{percent(value)} ({spoken} {noun})"


def date_ru(value: date) -> str:
    return value.strftime("%d.%m.%Y")


def date_words(value: date) -> str:
    return f"{value.day} {MONTHS_GENITIVE[value.month - 1]} {value.year} г."


def frequency_label(value: str) -> str:
    return FREQUENCY_LABELS[value]
