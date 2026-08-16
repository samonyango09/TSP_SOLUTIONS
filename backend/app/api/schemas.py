from datetime import date

from pydantic import BaseModel, ConfigDict

from app.churn import ChurnStatus
from app.db.models import LocationKind, MatchStatus, OutletSource, OutletType


class OutletRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: OutletSource
    outlet_type: OutletType
    name: str
    county: str
    town: str
    latitude: float | None
    longitude: float | None
    license_status: str
    has_pharmacy_service: bool


class OutletWithDistance(OutletRead):
    distance_km: float | None = None


class CustomerRead(BaseModel):
    id: str
    name: str
    total_sales_value: float
    num_orders: int
    average_order_value: float
    avg_purchase_interval_days: float | None
    last_order_date: date | None
    churn_status: ChurnStatus
    days_since_last_order: int | None


class CustomerWithLocation(CustomerRead):
    outlet: OutletRead | None = None
    distance_km: float | None = None


class MatchedOutlet(BaseModel):
    outlet: OutletRead
    confidence: float
    status: MatchStatus


class CustomerDetailRead(CustomerRead):
    first_order_date: date | None
    duration_as_customer_days: int | None
    yearly_sales: dict[str, float]
    quarterly_sales: dict[str, float]
    matched_outlets: list[MatchedOutlet]


class RoutePlanResponse(BaseModel):
    from_location: str
    to_location: str
    route_points: list[tuple[float, float]]
    buffer_km: float
    active_customers: list[CustomerWithLocation]
    at_risk_customers: list[CustomerWithLocation]
    churned_customers: list[CustomerWithLocation]
    prospects: list[OutletWithDistance]


class MatchRead(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    outlet_id: str
    outlet_name: str
    outlet_county: str
    confidence: float
    status: MatchStatus


class LocationSuggestion(BaseModel):
    name: str
    kind: LocationKind
    latitude: float
    longitude: float
    outlet_count: int
