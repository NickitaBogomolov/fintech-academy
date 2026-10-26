import calendar as _calendar
from collections.abc import Iterable
from datetime import date, timedelta

FIXED_HOLIDAYS: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
        (1, 7),
        (1, 8),
        (2, 23),
        (3, 8),
        (5, 1),
        (5, 9),
        (6, 12),
        (11, 4),
    }
)


class ProductionCalendar:
    def __init__(self, extra_holidays: Iterable[date] = (), extra_workdays: Iterable[date] = ()) -> None:
        self._extra_holidays = frozenset(extra_holidays)
        self._extra_workdays = frozenset(extra_workdays)

    def is_business_day(self, day: date) -> bool:
        if day in self._extra_workdays:
            return True
        if day in self._extra_holidays:
            return False
        if day.weekday() >= 5:
            return False
        return (day.month, day.day) not in FIXED_HOLIDAYS

    def following(self, day: date) -> date:
        while not self.is_business_day(day):
            day += timedelta(days=1)
        return day

    def preceding(self, day: date) -> date:
        while not self.is_business_day(day):
            day -= timedelta(days=1)
        return day

    def shift(self, day: date, business_days: int) -> date:
        step = 1 if business_days >= 0 else -1
        remaining = abs(business_days)
        while remaining:
            day += timedelta(days=step)
            if self.is_business_day(day):
                remaining -= 1
        return day


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    last_day = _calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last_day))
