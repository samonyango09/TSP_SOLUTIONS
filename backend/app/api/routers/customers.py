import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.schemas import CustomerDetailRead, CustomerRead, CustomerWithLocation, MatchedOutlet, OutletRead
from app.churn import ChurnStatus, classify_churn
from app.db.models import Customer, CustomerOutletMatch, MatchStatus, Outlet
from app.db.session import get_session

router = APIRouter(prefix="/api/customers", tags=["customers"])

_CONFIRMED_STATUSES = (MatchStatus.auto_confirmed, MatchStatus.manual_confirmed)


def _days_since(last_order: date | None, as_of: date) -> int | None:
    return (as_of - last_order).days if last_order else None


def _to_customer_read(customer: Customer, as_of: date) -> CustomerRead:
    return CustomerRead(
        id=customer.id,
        name=customer.name,
        total_sales_value=customer.total_sales_value,
        num_orders=customer.num_orders,
        average_order_value=customer.average_order_value,
        avg_purchase_interval_days=customer.avg_purchase_interval_days,
        last_order_date=customer.last_order_date,
        churn_status=classify_churn(customer, as_of),
        days_since_last_order=_days_since(customer.last_order_date, as_of),
    )


def _primary_outlet(session: Session, customer_id: str) -> Outlet | None:
    match = session.exec(
        select(CustomerOutletMatch)
        .where(CustomerOutletMatch.customer_id == customer_id, CustomerOutletMatch.status.in_(_CONFIRMED_STATUSES))
        .order_by(CustomerOutletMatch.confidence.desc())
    ).first()
    if not match:
        return None
    return session.get(Outlet, match.outlet_id)


@router.get("", response_model=list[CustomerWithLocation])
def list_customers(
    status: ChurnStatus | None = None,
    county: str | None = None,
    limit: int = Query(default=500, le=2000),
    offset: int = 0,
    session: Session = Depends(get_session),
):
    as_of = date.today()
    customers = session.exec(select(Customer).offset(offset).limit(limit)).all()

    results: list[CustomerWithLocation] = []
    for customer in customers:
        base = _to_customer_read(customer, as_of)
        if status is not None and base.churn_status != status:
            continue
        outlet = _primary_outlet(session, customer.id)
        if county and (not outlet or outlet.county != county):
            continue
        results.append(
            CustomerWithLocation(
                **base.model_dump(),
                outlet=OutletRead.model_validate(outlet) if outlet else None,
            )
        )
    return results


@router.get("/{customer_id}", response_model=CustomerDetailRead)
def get_customer(customer_id: str, session: Session = Depends(get_session)):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")

    as_of = date.today()
    base = _to_customer_read(customer, as_of)

    matches = session.exec(select(CustomerOutletMatch).where(CustomerOutletMatch.customer_id == customer_id)).all()
    matched_outlets = []
    for match in matches:
        outlet = session.get(Outlet, match.outlet_id)
        if outlet:
            matched_outlets.append(
                MatchedOutlet(outlet=OutletRead.model_validate(outlet), confidence=match.confidence, status=match.status)
            )

    return CustomerDetailRead(
        **base.model_dump(),
        first_order_date=customer.first_order_date,
        duration_as_customer_days=customer.duration_as_customer_days,
        yearly_sales=json.loads(customer.yearly_sales_json or "{}"),
        quarterly_sales=json.loads(customer.quarterly_sales_json or "{}"),
        matched_outlets=matched_outlets,
    )
