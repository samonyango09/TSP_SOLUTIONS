from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.api.schemas import LocationSuggestion
from app.db.models import LocationCentroid
from app.db.session import get_session

router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("/search", response_model=list[LocationSuggestion])
def search_locations(q: str = Query(min_length=1), limit: int = 10, session: Session = Depends(get_session)):
    pattern = f"%{q.strip()}%"
    rows = session.exec(
        select(LocationCentroid)
        .where(LocationCentroid.name.ilike(pattern))
        .order_by(LocationCentroid.outlet_count.desc())
        .limit(limit)
    ).all()
    return rows
