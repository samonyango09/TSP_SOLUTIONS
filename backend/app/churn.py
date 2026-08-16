"""Rule-based churn classification: how many of the customer's own typical
purchase cycles have elapsed since their last order.

The brief asks to "estimate if the customer is churned by duration passed
since last order" - this is exactly that, just normalized by each customer's
own historical cadence (a customer who orders every 10 days is churned much
sooner, in absolute days, than one who orders every 90) instead of a single
fixed day count for everyone. Deliberately not a learned model: there's no
labeled ground truth (confirmed lost accounts) yet to train one against, and
this rule directly satisfies the stated requirement - see docs/05-future-work.md.
"""

from datetime import date
from enum import StrEnum

from app.config import get_settings
from app.db.models import Customer


class ChurnStatus(StrEnum):
    active = "active"
    at_risk = "at_risk"
    churned = "churned"
    unknown = "unknown"


def churn_ratio(customer: Customer, as_of: date) -> float | None:
    if not customer.last_order_date or not customer.avg_purchase_interval_days:
        return None
    if customer.avg_purchase_interval_days <= 0:
        return None
    days_since = (as_of - customer.last_order_date).days
    return max(days_since, 0) / customer.avg_purchase_interval_days


def classify_churn(customer: Customer, as_of: date) -> ChurnStatus:
    ratio = churn_ratio(customer, as_of)
    if ratio is None:
        return ChurnStatus.unknown
    settings = get_settings()
    if ratio >= settings.churn_churned_ratio:
        return ChurnStatus.churned
    if ratio >= settings.churn_at_risk_ratio:
        return ChurnStatus.at_risk
    return ChurnStatus.active
