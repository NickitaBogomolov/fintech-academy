from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, computed_field


class CouponFrequency(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    AT_MATURITY = "at_maturity"

    @property
    def months(self) -> int | None:
        return {
            CouponFrequency.MONTHLY: 1,
            CouponFrequency.QUARTERLY: 3,
            CouponFrequency.SEMIANNUAL: 6,
            CouponFrequency.ANNUAL: 12,
            CouponFrequency.AT_MATURITY: None,
        }[self]


class BusinessDayRule(StrEnum):
    FOLLOWING = "following"
    PRECEDING = "preceding"


class RoundingMode(StrEnum):
    HALF_UP = "half_up"
    DOWN = "down"


class InvestorAccess(StrEnum):
    QUALIFIED_ONLY = "qualified_only"
    ALL = "all"


class Allocation(StrEnum):
    FIRST_COME = "first_come"
    PRO_RATA = "pro_rata"


class Issuer(BaseModel):
    inn: str
    ogrn: str
    full_name: str
    short_name: str
    code: str
    address: str
    director: str
    website: str
    rating: str | None = None


class IssueSpec(BaseModel):
    issue_number: str
    issuer: Issuer
    nominal: Decimal
    price: Decimal
    min_quantity: int
    max_quantity: int
    book_start: date
    book_end: date
    issue_date: date
    maturity_date: date
    coupon_rate: Decimal
    coupon_frequency: CouponFrequency
    business_day_rule: BusinessDayRule
    rounding_mode: RoundingMode
    early_redemption: bool
    investors: InvestorAccess
    allocation: Allocation

    @computed_field
    @property
    def min_amount(self) -> Decimal:
        return self.nominal * self.min_quantity

    @computed_field
    @property
    def max_amount(self) -> Decimal:
        return self.nominal * self.max_quantity

    @computed_field
    @property
    def term_days(self) -> int:
        return (self.maturity_date - self.issue_date).days
