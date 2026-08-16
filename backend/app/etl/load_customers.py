"""Loads the customer sales-analysis CSV into the Customer table.

The source file is already pre-aggregated (totals, averages, purchase
interval, yearly/quarterly breakdown) - this just reshapes it, it doesn't
recompute anything. Yearly (`sales_2022`) and quarterly (`sales_2023Q4`)
columns are detected by name and folded into JSON blobs rather than given
one rigid column each, so a future export with more quarters doesn't need a
schema migration.
"""

import csv
import json
import logging
import re
from datetime import date
from pathlib import Path

from sqlmodel import Session, delete

from app.config import get_settings
from app.db.models import Customer

logger = logging.getLogger(__name__)

_YEAR_COL = re.compile(r"^sales_(\d{4})$")
_QUARTER_COL = re.compile(r"^sales_(\d{4}Q\d)$")


def _parse_float(value: str) -> float:
    try:
        return float(value) if value not in (None, "") else 0.0
    except ValueError:
        return 0.0


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _read_csv(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def load_customers(session: Session, path: Path) -> int:
    session.exec(delete(Customer))
    session.commit()

    count = 0
    batch: list[Customer] = []
    for row in _read_csv(path):
        name = (row.get("customer") or "").strip()
        if not name:
            continue

        yearly: dict[str, float] = {}
        quarterly: dict[str, float] = {}
        for key, raw_value in row.items():
            if not raw_value:
                continue
            if m := _YEAR_COL.match(key):
                yearly[m.group(1)] = _parse_float(raw_value)
            elif m := _QUARTER_COL.match(key):
                quarterly[m.group(1)] = _parse_float(raw_value)

        duration_raw = row.get("duration_as_customer_days")
        customer = Customer(
            name=name,
            total_sales_value=_parse_float(row.get("total_sales_value", "")),
            num_orders=int(_parse_float(row.get("num_orders", ""))),
            average_order_value=_parse_float(row.get("average_order_value", "")),
            avg_purchase_interval_days=_parse_float(row.get("avg_purchase_interval_days", "")) or None,
            first_order_date=_parse_date(row.get("first_order_date", "")),
            last_order_date=_parse_date(row.get("last_order_date", "")),
            duration_as_customer_days=int(_parse_float(duration_raw)) if duration_raw else None,
            yearly_sales_json=json.dumps(yearly),
            quarterly_sales_json=json.dumps(quarterly),
        )
        batch.append(customer)
        count += 1

    session.add_all(batch)
    session.commit()
    logger.info("Loaded %d customers from %s", count, path)
    return count


def load_all_customers(session: Session) -> int:
    settings = get_settings()
    return load_customers(session, settings.customers_csv)
