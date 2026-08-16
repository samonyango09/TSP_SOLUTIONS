from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.schemas import MatchRead
from app.db.models import Customer, CustomerOutletMatch, MatchStatus, Outlet
from app.db.session import get_session

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchRead])
def list_matches(
    status: MatchStatus | None = Query(default=MatchStatus.suggested),
    session: Session = Depends(get_session),
):
    query = select(CustomerOutletMatch)
    if status is not None:
        query = query.where(CustomerOutletMatch.status == status)
    matches = session.exec(query.order_by(CustomerOutletMatch.confidence.desc())).all()

    results = []
    for match in matches:
        customer = session.get(Customer, match.customer_id)
        outlet = session.get(Outlet, match.outlet_id)
        if not customer or not outlet:
            continue
        results.append(
            MatchRead(
                id=match.id,
                customer_id=customer.id,
                customer_name=customer.name,
                outlet_id=outlet.id,
                outlet_name=outlet.name,
                outlet_county=outlet.county,
                confidence=match.confidence,
                status=match.status,
            )
        )
    return results


def _resolve(match_id: str, new_status: MatchStatus, session: Session) -> MatchRead:
    match = session.get(CustomerOutletMatch, match_id)
    if not match:
        raise HTTPException(404, "Match not found")
    match.status = new_status
    match.resolved_at = datetime.now(timezone.utc)
    session.add(match)
    session.commit()
    session.refresh(match)

    customer = session.get(Customer, match.customer_id)
    outlet = session.get(Outlet, match.outlet_id)
    return MatchRead(
        id=match.id,
        customer_id=match.customer_id,
        customer_name=customer.name if customer else "",
        outlet_id=match.outlet_id,
        outlet_name=outlet.name if outlet else "",
        outlet_county=outlet.county if outlet else "",
        confidence=match.confidence,
        status=match.status,
    )


@router.post("/{match_id}/confirm", response_model=MatchRead)
def confirm_match(match_id: str, session: Session = Depends(get_session)):
    return _resolve(match_id, MatchStatus.manual_confirmed, session)


@router.post("/{match_id}/reject", response_model=MatchRead)
def reject_match(match_id: str, session: Session = Depends(get_session)):
    return _resolve(match_id, MatchStatus.rejected, session)
