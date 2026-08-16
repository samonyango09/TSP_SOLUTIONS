"""One-shot ETL: load both outlet registers, load customers, fuzzy-match them,
derive location centroids - and print a data-quality summary so problems
(missing coordinates, unmatched customers, etc.) are visible immediately
instead of silently assumed fine.

Usage (from backend/):
    ./.venv/Scripts/python -m app.etl.run_all
"""

import logging
from collections import Counter

from sqlmodel import select

from app.db.models import Outlet, OutletType
from app.db.session import new_session
from app.etl.build_locations import build_locations
from app.etl.load_customers import load_all_customers
from app.etl.load_outlets import load_all_outlets
from app.etl.match_customers import match_customers

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> None:
    with new_session() as session:
        outlet_counts = load_all_outlets(session)
        customer_count = load_all_customers(session)
        match_stats = match_customers(session)
        location_counts = build_locations(session)

        outlets = session.exec(select(Outlet)).all()
        type_counts = Counter(o.outlet_type for o in outlets)
        county_coverage = sum(1 for o in outlets if o.county) / len(outlets) if outlets else 0.0
        geo_coverage = sum(1 for o in outlets if o.latitude and o.longitude) / len(outlets) if outlets else 0.0

    print("\n=== TSP Solutions ETL summary ===")
    print(f"Outlets loaded: {sum(outlet_counts.values())} ({outlet_counts})")
    for outlet_type in OutletType:
        print(f"  {outlet_type.value}: {type_counts.get(outlet_type, 0)}")
    print(f"  county coverage: {county_coverage:.0%}, geo coverage: {geo_coverage:.0%}")
    print(f"Customers loaded: {customer_count}")
    print(f"Customer-outlet matches: {match_stats}")
    print(f"Location centroids: {location_counts}")
    print("==================================\n")


if __name__ == "__main__":
    main()
