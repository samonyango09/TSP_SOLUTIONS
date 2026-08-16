from datetime import date

from app.churn import ChurnStatus, classify_churn, churn_ratio
from app.db.models import Customer


def _customer(**kwargs) -> Customer:
    defaults = dict(name="Test Pharmacy", avg_purchase_interval_days=30.0, last_order_date=date(2026, 6, 1))
    defaults.update(kwargs)
    return Customer(**defaults)


def test_active_when_ordering_within_typical_cadence():
    customer = _customer(last_order_date=date(2026, 8, 1))  # 14 days before as_of
    assert classify_churn(customer, as_of=date(2026, 8, 15)) == ChurnStatus.active


def test_at_risk_when_moderately_overdue():
    # 60 days since last order, avg interval 30 -> ratio 2.0, between 1.5 and 3.0
    customer = _customer(last_order_date=date(2026, 6, 16))
    assert classify_churn(customer, as_of=date(2026, 8, 15)) == ChurnStatus.at_risk


def test_churned_when_far_overdue():
    # ~150 days since last order, avg interval 30 -> ratio 5.0, well over 3.0
    customer = _customer(last_order_date=date(2026, 3, 18))
    assert classify_churn(customer, as_of=date(2026, 8, 15)) == ChurnStatus.churned


def test_unknown_when_no_purchase_history():
    customer = _customer(avg_purchase_interval_days=None, last_order_date=None)
    assert classify_churn(customer, as_of=date(2026, 8, 15)) == ChurnStatus.unknown
    assert churn_ratio(customer, as_of=date(2026, 8, 15)) is None


def test_churn_ratio_normalizes_by_customers_own_cadence():
    # Same 60-days-since-last-order for two customers with different typical
    # cadence should NOT classify the same way - that's the whole point of
    # using a ratio instead of one fixed day threshold for everyone.
    frequent_buyer = _customer(avg_purchase_interval_days=10.0, last_order_date=date(2026, 6, 16))
    infrequent_buyer = _customer(avg_purchase_interval_days=90.0, last_order_date=date(2026, 6, 16))
    as_of = date(2026, 8, 15)
    assert classify_churn(frequent_buyer, as_of) == ChurnStatus.churned
    assert classify_churn(infrequent_buyer, as_of) == ChurnStatus.active
