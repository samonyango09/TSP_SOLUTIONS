from sqlmodel import select

from app.db.models import Customer, CustomerOutletMatch, MatchStatus, Outlet, OutletSource, OutletType
from app.etl.match_customers import match_customers


def _outlet(name: str, outlet_type=OutletType.retail_pharmacy) -> Outlet:
    return Outlet(source=OutletSource.ppb_pharma, outlet_type=outlet_type, name=name, county="")


def test_distributor_customer_matches_multiple_branches_not_unrelated_outlets(session):
    # Regression case found during design: a single distributor customer
    # commonly corresponds to several separately PPB-registered branches, so
    # matching must be one-to-many, and it must not pick up unrelated outlets.
    customer = Customer(name="Medio-care Pharmaceuticals limited")
    session.add(customer)
    session.add_all(
        [
            _outlet("MEDIO CARE PHARMACEUTICALS - BONDO MARKET (Siaya)"),
            _outlet("MEDIO CARE PHARMACEUTICALS - KISUMU (Kisumu)"),
            _outlet("MEDIO CARE PHARMACEUTICALS BUSIA (Migori)"),
            _outlet("CUREWAVE PHARMACY"),
            _outlet("TULAGA CHEMIST LTD (Nyandarua)"),
        ]
    )
    session.commit()

    match_customers(session)

    matches = session.exec(select(CustomerOutletMatch).where(CustomerOutletMatch.customer_id == customer.id)).all()
    matched_names = set()
    for m in matches:
        outlet = session.get(Outlet, m.outlet_id)
        matched_names.add(outlet.name)

    assert "MEDIO CARE PHARMACEUTICALS - BONDO MARKET (Siaya)" in matched_names
    assert "MEDIO CARE PHARMACEUTICALS - KISUMU (Kisumu)" in matched_names
    assert "MEDIO CARE PHARMACEUTICALS BUSIA (Migori)" in matched_names
    assert "CUREWAVE PHARMACY" not in matched_names
    assert "TULAGA CHEMIST LTD (Nyandarua)" not in matched_names


def test_customer_with_no_plausible_match_gets_no_matches(session):
    # e.g. "Cash sales Vincent Osino" - a real ledger entry, not a registrable outlet.
    customer = Customer(name="Cash sales Vincent Osino")
    session.add(customer)
    session.add_all([_outlet("CUREWAVE PHARMACY"), _outlet("MEDIPLUS PHARMACY LTD")])
    session.commit()

    stats = match_customers(session)

    matches = session.exec(select(CustomerOutletMatch).where(CustomerOutletMatch.customer_id == customer.id)).all()
    assert matches == []
    assert stats["unmatched_customers"] >= 1


def test_near_exact_name_is_auto_confirmed(session):
    customer = Customer(name="Curewave Pharmacy")
    session.add(customer)
    session.add(_outlet("CUREWAVE PHARMACY"))
    session.commit()

    match_customers(session)

    matches = session.exec(select(CustomerOutletMatch).where(CustomerOutletMatch.customer_id == customer.id)).all()
    assert len(matches) == 1
    assert matches[0].status == MatchStatus.auto_confirmed
