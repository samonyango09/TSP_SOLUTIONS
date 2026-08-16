"""Derives town/county centroids from the loaded Outlet table, so the route
planner's from/to search doesn't depend on an external geocoder for the
common case of "a Kenyan town or county name" - the outlet data already
covers all 47 counties and thousands of towns.
"""

import logging
from collections import defaultdict

from sqlmodel import Session, delete, select

from app.db.models import LocationCentroid, LocationKind, Outlet

logger = logging.getLogger(__name__)


def _centroids_for(rows: list[tuple[str, float, float]]) -> dict[str, tuple[float, float, int]]:
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0])
    for name, lat, lon in rows:
        if not name:
            continue
        bucket = sums[name]
        bucket[0] += lat
        bucket[1] += lon
        bucket[2] += 1
    return {name: (lat_sum / n, lon_sum / n, n) for name, (lat_sum, lon_sum, n) in sums.items()}


def build_locations(session: Session) -> dict[str, int]:
    session.exec(delete(LocationCentroid))
    session.commit()

    outlets = session.exec(
        select(Outlet.town, Outlet.county, Outlet.latitude, Outlet.longitude).where(
            Outlet.latitude.is_not(None), Outlet.longitude.is_not(None)
        )
    ).all()

    town_rows = [(town, lat, lon) for town, _county, lat, lon in outlets]
    county_rows = [(county, lat, lon) for _town, county, lat, lon in outlets]

    batch: list[LocationCentroid] = []
    for name, (lat, lon, n) in _centroids_for(town_rows).items():
        batch.append(LocationCentroid(name=name, kind=LocationKind.town, latitude=lat, longitude=lon, outlet_count=n))
    for name, (lat, lon, n) in _centroids_for(county_rows).items():
        batch.append(
            LocationCentroid(name=name, kind=LocationKind.county, latitude=lat, longitude=lon, outlet_count=n)
        )

    session.add_all(batch)
    session.commit()
    counts = {"towns": len(_centroids_for(town_rows)), "counties": len(_centroids_for(county_rows))}
    logger.info("Built %d town centroids, %d county centroids", counts["towns"], counts["counties"])
    return counts
