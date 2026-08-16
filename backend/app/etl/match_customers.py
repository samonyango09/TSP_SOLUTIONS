"""Fuzzy-links Customer rows to Outlet rows by name.

Plain string-similarity ratio (tested with stdlib difflib during design)
performs poorly here because a single distributor customer commonly
corresponds to *several* separately PPB-registered branches, e.g.
"Medio-care Pharmaceuticals limited" -> "MEDIO CARE PHARMACEUTICALS -
BONDO MARKET (Siaya)", "MEDIO CARE PHARMACEUTICALS - KISUMU (Kisumu)", etc.
rapidfuzz's token_set_ratio tolerates the extra branch/county tokens far
better than a whole-string ratio, and this is deliberately one-to-many: every
candidate above the suggest threshold is kept as its own match row, not just
the single best one.

token_set_ratio alone isn't enough, though - verified directly against the
real data that it silently mismatches two *different* companies that just
share a generic suffix, e.g. "Fountain healthcare limited" vs "CBM HEALTHCARE
LIMITED" scores 90 (comfortably auto-confirm) purely off "HEALTHCARE LIMITED"
overlap, and separately *misses* real matches like "Philmed Pharmaceutical"
vs "PHILMED LIMITED-UMOJA (Nairobi)" (scores only 48, since two mostly-
different bags of tokens outweigh the one that actually identifies the
business). Both are fixed by a distinctive-token guard: strip common
pharma/business words first, then require at least one of the customer's
*remaining* (brand-identifying) tokens to appear verbatim in the outlet name
before a candidate counts as a match at all.

The guard is applied as a *candidate-generation* step (an inverted token
index), not a post-filter on rapidfuzz's top-N - an earlier version scored
all ~28k outlets per customer and kept the top 50 by raw token_set_ratio
before checking the guard, which silently dropped real low-score-but-correct
matches like Philmed's: with a generous score cutoff, enough unrelated
outlets coincidentally out-scored it on shared generic words alone (e.g.
"...PHARMACEUTICALS LIMITED...") to push it out of the top 50 before the
guard ever saw it. Building the candidate set from the index instead
guarantees every guard-passing outlet gets scored, and it's cheaper too
(no need to score every outlet against every customer). The token_set_ratio
score is then only used to grade confidence among guard-passing candidates.

Some customer rows (e.g. "Cash sales Vincent Osino") are not registrable
outlets at all and will legitimately end up with zero matches - that's
expected, not a bug to chase.
"""

import logging
import re
from collections import defaultdict

from rapidfuzz import fuzz
from sqlmodel import Session, delete, select

from app.config import get_settings
from app.db.models import Customer, CustomerOutletMatch, MatchMethod, MatchStatus, Outlet

logger = logging.getLogger(__name__)

_SCORE_FLOOR = 55.0

# Safety net beyond the static _GENERIC_WORDS list: any token (typo variant,
# place name, etc.) whose index bucket is this large can't be distinctive
# either, whether or not it made the stoplist - skip it as a guard token
# rather than let it turn into a scoring pass over hundreds of outlets.
_MAX_BUCKET_SIZE = 300

_NON_ALNUM = re.compile(r"[^A-Z0-9]+")

# Generic pharma/business words that appear in enough names to be useless as
# a "this is the same company" signal on their own - excluded when picking
# each customer's distinctive (brand-identifying) tokens for the guard.
_GENERIC_WORDS = {
    "PHARMACY",
    "PHARMACEUTICAL",
    "PHARMACEUTICALS",
    "CHEMIST",
    "CHEMISTS",
    "HEALTHCARE",
    "HEALTH",
    "CARE",
    "MEDICAL",
    "MEDICALS",
    "MEDICARE",
    "MEDICINE",
    "MEDICENTRE",
    "DRUGS",
    "DISTRIBUTORS",
    "DISTRIBUTOR",
    "WHOLESALE",
    "WHOLESALERS",
    "RETAIL",
    "ENTERPRISES",
    "ENTERPRISE",
    "COMPANY",
    "GROUP",
    "HOLDINGS",
    "LIMITED",
    "LTD",
    "LLP",
    "INC",
    "CO",
    "AND",
    "THE",
    # Facility-type/descriptor words that are extremely common across the
    # ~17.6k-row hospital register on their own (e.g. hundreds of "... Clinic"
    # entries) - without excluding these, a customer name that happens to
    # contain one turns into an index lookup over thousands of unrelated
    # outlets, most of which coincidentally clear the score floor.
    "CLINIC",
    "CLINICS",
    "DISPENSARY",
    "DISPENSARIES",
    "HOSPITAL",
    "HOSPITALS",
    "CENTRE",
    "CENTER",
    "CENTERS",
    "CENTRES",
    "SERVICES",
    "SERVICE",
    "NURSING",
    "MATERNITY",
    "HOME",
    "FACILITY",
    "FACILITIES",
    "OUTLET",
    "OUTLETS",
    "SHOP",
    "STORES",
    "STORE",
}


def _normalize(name: str) -> str:
    # Punctuation (hyphens, parens, "&") becomes a token boundary, not part of
    # a token, so "Medio-care" lines up with a register entry's "MEDIO CARE" -
    # without this, token_set_ratio scores every real branch match well below
    # a usable threshold (verified: ~65 with punctuation kept vs ~87 without).
    return " ".join(_NON_ALNUM.sub(" ", name.upper()).split())


def _distinctive_tokens(normalized_name: str) -> set[str]:
    tokens = set(normalized_name.split())
    distinctive = tokens - _GENERIC_WORDS
    return distinctive or tokens  # if every token is generic, fall back to all of them


def _build_token_index(outlet_token_sets: list[set[str]]) -> dict[str, list[int]]:
    index: dict[str, list[int]] = defaultdict(list)
    for idx, tokens in enumerate(outlet_token_sets):
        for token in tokens:
            index[token].append(idx)
    return index


def match_customers(session: Session) -> dict[str, int]:
    settings = get_settings()
    session.exec(delete(CustomerOutletMatch))
    session.commit()

    customers = session.exec(select(Customer)).all()
    outlets = session.exec(select(Outlet)).all()
    outlet_names = [_normalize(o.name) for o in outlets]
    outlet_token_sets = [set(n.split()) for n in outlet_names]
    token_index = _build_token_index(outlet_token_sets)

    stats = {"auto_confirmed": 0, "suggested": 0, "unmatched_customers": 0}
    batch: list[CustomerOutletMatch] = []

    for customer in customers:
        query = _normalize(customer.name)
        if query in {"CASH SALES", ""}:
            stats["unmatched_customers"] += 1
            continue
        customer_distinctive = _distinctive_tokens(query)

        candidate_indices: set[int] = set()
        for token in customer_distinctive:
            bucket = token_index.get(token, ())
            if len(bucket) > _MAX_BUCKET_SIZE:
                continue
            candidate_indices.update(bucket)

        matched_any = False
        for idx in candidate_indices:
            score = fuzz.token_set_ratio(query, outlet_names[idx])
            if score < _SCORE_FLOOR:
                continue
            matched_any = True
            outlet = outlets[idx]
            status = (
                MatchStatus.auto_confirmed
                if score >= settings.match_auto_confirm_threshold
                else MatchStatus.suggested
            )
            stats["auto_confirmed" if status == MatchStatus.auto_confirmed else "suggested"] += 1
            batch.append(
                CustomerOutletMatch(
                    customer_id=customer.id,
                    outlet_id=outlet.id,
                    confidence=round(score, 2),
                    match_method=MatchMethod.token_fuzzy,
                    status=status,
                )
            )

        if not matched_any:
            stats["unmatched_customers"] += 1

    session.add_all(batch)
    session.commit()
    logger.info(
        "Matched customers: %d auto-confirmed, %d suggested, %d customers with no guard-passing candidate",
        stats["auto_confirmed"],
        stats["suggested"],
        stats["unmatched_customers"],
    )
    return stats
