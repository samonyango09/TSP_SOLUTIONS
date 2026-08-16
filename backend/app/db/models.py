import uuid
from datetime import date, datetime, timezone
from enum import StrEnum

from sqlmodel import Field, SQLModel


def _uid() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OutletSource(StrEnum):
    ppb_pharma = "ppb_pharma"
    kmhfr_hospital = "kmhfr_hospital"


class OutletType(StrEnum):
    distributor = "distributor"
    retail_pharmacy = "retail_pharmacy"
    hospital = "hospital"
    hospital_with_pharmacy = "hospital_with_pharmacy"


class Outlet(SQLModel, table=True):
    id: str = Field(default_factory=_uid, primary_key=True)
    source: OutletSource = Field(index=True)
    outlet_type: OutletType = Field(index=True)
    name: str = Field(index=True)
    county: str = Field(default="", index=True)
    town: str = Field(default="")
    latitude: float | None = None
    longitude: float | None = None
    license_status: str = ""
    # True for hospitals that have a service under the "PHARMACY SERVICES" category
    # in the KMHFR services_json - i.e. a "hospital with a pharmacy in it", called
    # out in the brief as a distinct prospect type from a plain registered hospital.
    has_pharmacy_service: bool = False
    # Source-specific fields that don't merit their own column on the unified
    # table (PPB registration numbers, KMHFR bed counts, etc.), kept for detail
    # views without forcing every source into the same rigid schema.
    raw_extra_json: str = "{}"
    created_at: datetime = Field(default_factory=_now)


class Customer(SQLModel, table=True):
    id: str = Field(default_factory=_uid, primary_key=True)
    name: str = Field(index=True)
    total_sales_value: float = 0.0
    num_orders: int = 0
    average_order_value: float = 0.0
    avg_purchase_interval_days: float | None = None
    first_order_date: date | None = None
    last_order_date: date | None = None
    duration_as_customer_days: int | None = None
    # Sparse {"2022": 201600.0, "2023": ...} / {"2022Q3": ..., ...} straight from
    # the source CSV's yearly/quarterly columns - kept as JSON rather than one
    # rigid column per period so a new quarter in a future export doesn't
    # require a schema migration.
    yearly_sales_json: str = "{}"
    quarterly_sales_json: str = "{}"
    created_at: datetime = Field(default_factory=_now)


class MatchMethod(StrEnum):
    exact = "exact"
    token_fuzzy = "token_fuzzy"


class MatchStatus(StrEnum):
    suggested = "suggested"
    auto_confirmed = "auto_confirmed"
    manual_confirmed = "manual_confirmed"
    rejected = "rejected"


class CustomerOutletMatch(SQLModel, table=True):
    id: str = Field(default_factory=_uid, primary_key=True)
    customer_id: str = Field(foreign_key="customer.id", index=True)
    outlet_id: str = Field(foreign_key="outlet.id", index=True)
    confidence: float = 0.0
    match_method: MatchMethod = MatchMethod.token_fuzzy
    status: MatchStatus = Field(default=MatchStatus.suggested, index=True)
    created_at: datetime = Field(default_factory=_now)
    resolved_at: datetime | None = None


class LocationKind(StrEnum):
    town = "town"
    county = "county"


class LocationCentroid(SQLModel, table=True):
    id: str = Field(default_factory=_uid, primary_key=True)
    name: str = Field(index=True)
    kind: LocationKind = Field(index=True)
    latitude: float
    longitude: float
    outlet_count: int = 0
