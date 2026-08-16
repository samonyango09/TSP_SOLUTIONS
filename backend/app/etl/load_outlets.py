"""Loads the two source registers (PPB pharma outlets, KMHFR hospitals) into
the unified Outlet table.

Kept deliberately dependency-light (stdlib csv/json, no pandas) since both
files are just being streamed row-by-row into SQLite once - a DataFrame
wouldn't buy much here and the hospitals CSV is large enough (~85MB, mostly
services_json) that loading it all into memory at once is worth avoiding.
"""

import csv
import json
import logging
from pathlib import Path

from sqlmodel import Session, delete

from app.config import get_settings
from app.db.models import Outlet, OutletSource, OutletType

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500

_PHARMA_TYPE_MAP = {
    "wholesale": OutletType.distributor,
    "retail": OutletType.retail_pharmacy,
    "hospital": OutletType.hospital,
}


def _read_csv(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)


def load_pharma_outlets(session: Session, path: Path) -> int:
    count = 0
    batch: list[Outlet] = []
    for row in _read_csv(path):
        outlet_type = _PHARMA_TYPE_MAP.get((row.get("facility_type") or "").strip().lower())
        if outlet_type is None:
            continue
        lat, lon = row.get("geo_latitude"), row.get("geo_longitude")
        extra = {
            "registration_number": row.get("registration_number", ""),
            "detail_ownership": row.get("detail_ownership", ""),
            "detail_license_type": row.get("detail_license_type", ""),
            "detail_establishment_year": row.get("detail_establishment_year", ""),
            "detail_superintendent_name": row.get("detail_superintendent_name", ""),
            "detail_valid_till": row.get("detail_valid_till", ""),
        }
        outlet = Outlet(
            source=OutletSource.ppb_pharma,
            outlet_type=outlet_type,
            name=(row.get("facility_name") or "").strip(),
            county=(row.get("detail_county") or "").strip(),
            town=(row.get("detail_town") or "").strip(),
            latitude=float(lat) if lat else None,
            longitude=float(lon) if lon else None,
            license_status=(row.get("license_status") or "").strip(),
            has_pharmacy_service=False,
            raw_extra_json=json.dumps(extra),
        )
        batch.append(outlet)
        count += 1
        if len(batch) >= _BATCH_SIZE:
            session.add_all(batch)
            session.commit()
            batch.clear()
    if batch:
        session.add_all(batch)
        session.commit()
    logger.info("Loaded %d PPB pharma outlets from %s", count, path)
    return count


def _has_pharmacy_service(services_json_raw: str) -> bool:
    if not services_json_raw:
        return False
    try:
        services = json.loads(services_json_raw)
    except (json.JSONDecodeError, TypeError):
        return False
    return any("PHARMACY" in (s.get("category_name") or "").upper() for s in services)


def load_hospitals(session: Session, path: Path) -> int:
    count = 0
    batch: list[Outlet] = []
    for row in _read_csv(path):
        lat, lon = row.get("latitude"), row.get("longitude")
        has_pharmacy = _has_pharmacy_service(row.get("services_json", ""))
        extra = {
            "code": row.get("code", ""),
            "facility_type_name": row.get("facility_type_name", ""),
            "owner_name": row.get("owner_name", ""),
            "owner_type_name": row.get("owner_type_name", ""),
            "keph_level_name": row.get("keph_level_name", ""),
            "number_of_beds": row.get("number_of_beds", ""),
            "operation_status_name": row.get("operation_status_name", ""),
        }
        outlet = Outlet(
            source=OutletSource.kmhfr_hospital,
            outlet_type=OutletType.hospital_with_pharmacy if has_pharmacy else OutletType.hospital,
            name=(row.get("name") or "").strip(),
            county=(row.get("county_name") or "").strip(),
            town=(row.get("town_name") or "").strip(),
            latitude=float(lat) if lat else None,
            longitude=float(lon) if lon else None,
            license_status=(row.get("regulatory_status_name") or "").strip(),
            has_pharmacy_service=has_pharmacy,
            raw_extra_json=json.dumps(extra),
        )
        batch.append(outlet)
        count += 1
        if len(batch) >= _BATCH_SIZE:
            session.add_all(batch)
            session.commit()
            batch.clear()
    if batch:
        session.add_all(batch)
        session.commit()
    logger.info("Loaded %d KMHFR hospitals from %s", count, path)
    return count


def load_all_outlets(session: Session) -> dict[str, int]:
    settings = get_settings()
    session.exec(delete(Outlet))
    session.commit()
    pharma_count = load_pharma_outlets(session, settings.pharma_outlets_csv)
    hospital_count = load_hospitals(session, settings.hospitals_csv)
    return {"pharma_outlets": pharma_count, "hospitals": hospital_count}
