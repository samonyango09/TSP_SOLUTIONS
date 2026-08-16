# Backend tutorial

A deep dive into how the backend works and why, for future reference - not just what each file
does (the code itself says that) but the concepts and reasoning behind it.

## Stack

- **FastAPI** - the HTTP framework. Path operation functions (`@router.get(...)` etc.) declare
  their parameters and response shape with Python type hints; FastAPI turns those into request
  validation, response serialization, and auto-generated OpenAPI docs (visit
  `http://127.0.0.1:8000/docs` while the server is running) for free.
- **SQLModel** - a thin layer that makes a single Python class (e.g. `Outlet` in
  `app/db/models.py`) work as both a Pydantic validation model *and* a SQLAlchemy ORM table
  (`table=True`). One class, no separate "DB model" vs "API model" duplication for internal state
  (the API-facing shapes in `app/api/schemas.py` are still separate, deliberately - see below).
- **SQLite** - the whole database is one file (`workspace/app.db`). Zero setup, fine for this
  project's scale (a few tens of thousands of rows); `04-deployment.md` covers when/how to swap in
  Postgres.
- **rapidfuzz** - a fast (C++-backed) fuzzy string matching library, used for the customer-to-
  outlet name matching.

## Why `api/schemas.py` is separate from `db/models.py`

`db/models.py` defines what's *stored*. `api/schemas.py` defines what's *returned over HTTP*. They
often look similar (`OutletRead` mirrors most of `Outlet`) but keeping them separate means the
database schema can gain internal-only fields (or change shape) without automatically changing the
API contract, and response shapes can combine/reshape data from multiple tables (e.g.
`CustomerWithLocation` bolts an `Outlet` onto a `Customer`, `RoutePlanResponse` combines four
different queries into one payload) without contorting the table definitions to match.

One subtlety worth knowing: Pydantic v2 models don't accept arbitrary Python objects (like a
SQLModel ORM row) via `.model_validate()` unless you tell them to. `OutletRead` sets
`model_config = ConfigDict(from_attributes=True)` for exactly this reason - without it,
`OutletRead.model_validate(some_outlet_row)` raises a validation error, which is a real bug we hit
and fixed while building this (see `00-discovery-and-design.md`... actually see the git history /
this note, since it was caught during manual testing, not code review). FastAPI's own response-
model serialization (returning an ORM object directly from a path operation with
`response_model=...`) handles this automatically regardless of the model's own config - the
explicit config was needed for the *manual* `.model_validate()` calls in `customers.py` and
`route_plan.py`.

## The ETL pipeline (`app/etl/`)

Run as `python -m app.etl.run_all` (see `run_all.py`). Four steps, each independently testable and
re-runnable (they all `delete` their own table's rows first, so re-running is idempotent):

1. **`load_outlets.py`** - streams both source CSVs row-by-row (plain `csv.DictReader`, no pandas -
   the hospitals CSV alone is ~85MB, mostly `services_json` blobs, so loading it all into a
   DataFrame first wouldn't buy anything here) into the unified `Outlet` table, batching commits
   every 500 rows for throughput. `_has_pharmacy_service()` parses each hospital's `services_json`
   and checks for a `category_name` containing "PHARMACY" - that's the entire "hospital with a
   pharmacy in it" feature; no separate dataset or manual list needed.
2. **`load_customers.py`** - reshapes the pre-aggregated customer CSV. Notice the yearly
   (`sales_2022`) and quarterly (`sales_2023Q4`) columns are detected by regex
   (`_YEAR_COL`/`_QUARTER_COL`) and folded into two JSON blobs (`yearly_sales_json`,
   `quarterly_sales_json`) rather than given one rigid database column each - a future export with
   an extra quarter just works, no migration needed.
3. **`match_customers.py`** - the most involved piece; read its module docstring first, it
   documents three iterations of a real bug hunt (over-matching, under-matching, then over-matching
   again) with the actual data that exposed each one. The core technique worth understanding even
   outside this project:
   - **Token-set fuzzy scoring** (`rapidfuzz.fuzz.token_set_ratio`) treats a name as a *set* of
     words rather than a fixed sequence, so extra words (a branch suffix, a county in parens) hurt
     the score much less than they would with a plain edit-distance ratio.
   - **A distinctive-token guard** as a precision floor: strip generic words (LIMITED, PHARMACY,
     CLINIC, ...) from a name, and require at least one of what's left to appear verbatim in the
     candidate before it's considered at all. This catches the case token-set scoring alone misses:
     two different businesses that happen to share only generic words.
   - **An inverted index for candidate generation, not filtering.** `_build_token_index()` builds a
     `dict[token, [outlet indices]]`. For each customer, the candidate set is the union of
     `token_index[token]` for each of that customer's distinctive tokens - so *every* outlet
     sharing a distinctive word gets scored, guaranteed, rather than hoping a real match survives
     being ranked against everything else in the database. This is also just faster: instead of
     scoring every customer against all ~28k outlets, each customer is scored only against outlets
     that share a meaningful word with it.
   - **A dynamic bucket-size cap** (`_MAX_BUCKET_SIZE`) as a safety net beyond the static stoplist -
     any token indexing more than 300 outlets gets skipped as a guard token regardless of whether
     it's on the stoplist, since a word that common can't be distinctive either way.
4. **`build_locations.py`** - averages every outlet's lat/lon by town and by county into
   `LocationCentroid` rows, which is what the route planner's from/to search autocompletes against
   (see `locations.py` router) - no external geocoding API needed for "a Kenyan town or county
   name," since the outlet data already covers that.

## Geo math (`app/geo.py`)

No GIS library dependency (shapely, geopandas) - at this scale, plain trigonometry is fast enough
and keeps the dependency list short:

- `haversine_km()` - great-circle distance between two lat/lon points on a sphere. Standard
  formula; look it up if the trig is unfamiliar, it's not specific to this project.
- `distance_to_segment_km()` - the more interesting one. To find how far a point is from a *route*
  (not just a single point), you need point-to-line-segment distance, which is normally 2D
  Euclidean geometry - but lat/lon aren't a flat 2D plane. `_to_local_xy()` does a simple
  equirectangular projection (treat degrees-of-longitude as scaled by `cos(latitude)` to
  approximate a flat plane) centered on the segment's start point. This approximation only holds
  over short distances, which is exactly what a single route segment is - it would *not* be
  accurate for, say, the distance between Nairobi and London.
- `distance_to_route_km()` - a route is a polyline (list of lat/lon points from OSRM, or just two
  points for the straight-line fallback); this checks every segment and returns the minimum
  distance, which is what "how far is this outlet from the route" means.

## Churn rule (`app/churn.py`)

`churn_ratio()` = days since the customer's last order, divided by that *same customer's* average
purchase interval. A customer who normally orders every 10 days is meaningfully overdue at 30 days
(ratio 3.0); a customer who normally orders every 90 days is not (ratio 0.33). This normalization
is the whole point - a single fixed "90 days = churned" threshold would misclassify both of them.
`classify_churn()` then buckets that ratio against two configurable thresholds
(`churn_at_risk_ratio`, `churn_churned_ratio` in `app/config.py`).

## Auth (`app/auth.py`)

A signed cookie (`itsdangerous.URLSafeSerializer`), not a JWT or session-store - there's exactly
one piece of state to protect ("is this browser allowed in at all"), so a cryptographically signed
cookie the server can verify without a database lookup is the simplest thing that works.
`require_session` is wired as a router-level FastAPI dependency
(`app.include_router(..., dependencies=[Depends(require_session)])` in `main.py`), which runs it
before every request to that router without repeating the check in each path operation.
