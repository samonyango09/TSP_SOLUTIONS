from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.api.schemas import OutletRead
from app.db.models import Outlet, OutletType
from app.db.session import get_session

router = APIRouter(prefix="/api/outlets", tags=["outlets"])

_MAX_LIMIT = 2000


@router.get("", response_model=list[OutletRead])
def list_outlets(
    outlet_type: OutletType | None = Query(default=None, alias="type"),
    county: str | None = None,
    limit: int = Query(default=500, le=_MAX_LIMIT),
    offset: int = 0,
    session: Session = Depends(get_session),
):
    query = select(Outlet)
    if outlet_type is not None:
        query = query.where(Outlet.outlet_type == outlet_type)
    if county:
        query = query.where(Outlet.county == county)
    query = query.offset(offset).limit(limit)
    return session.exec(query).all()


@router.get("/facets")
def outlet_facets(session: Session = Depends(get_session)) -> dict:
    counties = session.exec(
        select(Outlet.county).where(Outlet.county != "").distinct().order_by(Outlet.county)
    ).all()
    return {
        "types": [t.value for t in OutletType],
        "counties": [c for c in counties if c],
    }
