from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.schemas import CustomerWithLocation, OutletRead, OutletWithDistance, RoutePlanResponse
from app.churn import ChurnStatus, classify_churn
from app.config import get_settings
from app.db.models import Customer, CustomerOutletMatch, LocationCentroid, MatchStatus, Outlet
from app.db.session import get_session
from app.geo import distance_to_route_km
from app.routing import get_route_points

router = APIRouter(prefix="/api/route-plan", tags=["route-plan"])

_CONFIRMED_STATUSES = (MatchStatus.auto_confirmed, MatchStatus.manual_confirmed)


def _resolve_location(session: Session, name: str) -> LocationCentroid:
    pattern = f"%{name.strip()}%"
    match = session.exec(
        select(LocationCentroid).where(LocationCentroid.name.ilike(pattern)).order_by(LocationCentroid.outlet_count.desc())
    ).first()
    if not match:
        raise HTTPException(404, f"No known location matching {name!r}")
    return match


def _bbox(route_points: list[tuple[float, float]], buffer_km: float) -> tuple[float, float, float, float]:
    lats = [p[0] for p in route_points]
    lons = [p[1] for p in route_points]
    pad_lat = buffer_km / 111.0  # ~111km per degree latitude
    pad_lon = buffer_km / 90.0  # generous pad for longitude convergence near the equator
    return (min(lats) - pad_lat, max(lats) + pad_lat, min(lons) - pad_lon, max(lons) + pad_lon)


@router.get("", response_model=RoutePlanResponse)
def plan_route(
    from_: str = Query(alias="from"),
    to: str = Query(),
    buffer_km: float | None = None,
    session: Session = Depends(get_session),
):
    settings = get_settings()
    buffer_km = buffer_km or settings.route_buffer_km_default

    from_loc = _resolve_location(session, from_)
    to_loc = _resolve_location(session, to)
    route_points = get_route_points(from_loc.latitude, from_loc.longitude, to_loc.latitude, to_loc.longitude)

    min_lat, max_lat, min_lon, max_lon = _bbox(route_points, buffer_km)
    as_of = date.today()

    matched_outlet_ids: set[str] = set()
    active: list[CustomerWithLocation] = []
    at_risk: list[CustomerWithLocation] = []
    churned: list[CustomerWithLocation] = []

    matches = session.exec(
        select(CustomerOutletMatch).where(CustomerOutletMatch.status.in_(_CONFIRMED_STATUSES))
    ).all()
    for match in matches:
        outlet = session.get(Outlet, match.outlet_id)
        if not outlet or outlet.latitude is None or outlet.longitude is None:
            continue
        matched_outlet_ids.add(outlet.id)
        if not (min_lat <= outlet.latitude <= max_lat and min_lon <= outlet.longitude <= max_lon):
            continue
        distance = distance_to_route_km(outlet.latitude, outlet.longitude, route_points)
        if distance > buffer_km:
            continue

        customer = session.get(Customer, match.customer_id)
        if not customer:
            continue
        status = classify_churn(customer, as_of)
        entry = CustomerWithLocation(
            id=customer.id,
            name=customer.name,
            total_sales_value=customer.total_sales_value,
            num_orders=customer.num_orders,
            average_order_value=customer.average_order_value,
            avg_purchase_interval_days=customer.avg_purchase_interval_days,
            last_order_date=customer.last_order_date,
            churn_status=status,
            days_since_last_order=(as_of - customer.last_order_date).days if customer.last_order_date else None,
            outlet=OutletRead.model_validate(outlet),
            distance_km=round(distance, 2),
        )
        if status == ChurnStatus.churned:
            churned.append(entry)
        elif status == ChurnStatus.at_risk:
            at_risk.append(entry)
        else:
            active.append(entry)

    prospects: list[OutletWithDistance] = []
    candidates = session.exec(
        select(Outlet).where(
            Outlet.latitude.is_not(None),
            Outlet.longitude.is_not(None),
            Outlet.latitude >= min_lat,
            Outlet.latitude <= max_lat,
            Outlet.longitude >= min_lon,
            Outlet.longitude <= max_lon,
        )
    ).all()
    for outlet in candidates:
        if outlet.id in matched_outlet_ids:
            continue
        distance = distance_to_route_km(outlet.latitude, outlet.longitude, route_points)
        if distance > buffer_km:
            continue
        prospects.append(OutletWithDistance(**OutletRead.model_validate(outlet).model_dump(), distance_km=round(distance, 2)))

    return RoutePlanResponse(
        from_location=from_loc.name,
        to_location=to_loc.name,
        route_points=route_points,
        buffer_km=buffer_km,
        active_customers=sorted(active, key=lambda c: c.distance_km or 0),
        at_risk_customers=sorted(at_risk, key=lambda c: c.distance_km or 0),
        churned_customers=sorted(churned, key=lambda c: c.distance_km or 0),
        prospects=sorted(prospects, key=lambda o: o.distance_km or 0),
    )
