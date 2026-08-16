# Discovery & Design

## The brief

`TSP Solutions.docx` asks for a Pharma Sales System that helps a sales team:

1. Enter a route (e.g. "Nairobi to Meru") and see every active/churned customer along it, with
   sales history, average order value, purchase interval, and yearly/quarterly sales.
2. Browse prospective outlets - key distributors, major hospitals, major retail pharmacies - in a
   region without a route, filterable by outlet type and county.
3. Run as a free-hosted web app for up to ~10k users in year one, built through a full
   Discovery -> Design -> Build -> Deploy -> Support/Scale process, using AI-engineering concepts
   (RAG, MCP, agents, ML) "to the extent to which they are necessary," with reasoning documented
   for every non-obvious decision.

This document is that reasoning.

## Scope-defining decisions

Three decisions were made explicitly with the project owner before building anything, since the
brief left them open on purpose ("recommend if you will need logins... I am open to using Azure or
AWS provided it won't break the bank"):

| Decision | Choice | Why |
|---|---|---|
| Hosting | Free-tier only | The brief's primary ask is "hosted on a free platform" for a ~10k-user first year; Azure/AWS free tiers were the fallback option but weren't needed to meet that scale. |
| Customer-to-outlet linking | Fuzzy-match automatically, queue uncertain matches for human review | The customer sales CSV has no location data at all - only outlet name and sales numbers - so *some* form of linking to the geocoded registers is required to put a customer on a map. Fuzzy matching is the only option (zero customer names matched a register exactly - see below); requiring only exact matches would leave the map nearly empty, and silently trusting every fuzzy match would put wrong customers on wrong locations. |
| Map/geocoding | OpenStreetMap + Leaflet, no API key | Matches "hosted on a free platform" directly - Google Maps' free tier requires a billing account and caps out with real usage; OSM has neither cost. |

## What the source data actually looks like

Before designing anything, the three source files were inspected directly (not assumed):

- **`Geocoded Registered Pharmaceutical Outlets in Kenya.csv`** (10,647 rows, from the PPB
  register) - `facility_type` is one of `retail`, `wholesale`, `hospital`; 99.8% have lat/lon; only
  ~71% have a `detail_county` filled in.
- **`Registered Hospitals in Kenya.csv`** (17,588 rows, from KMHFR) - 97% have lat/lon, all 47
  counties represented (well, 48 distinct county *strings* - "Murang'a" and "Muranga" both appear
  in the source data as separate spellings; left as-is rather than silently merged, since a wrong
  guess at which is canonical could misfile facilities). Each row carries a `services_json` blob
  listing that facility's services with a `category_name` - hospitals with a category containing
  "PHARMACY" (e.g. "Hospital-Retail Service") are exactly the brief's "hospitals with pharmacies in
  them," so that's a derived boolean (`Outlet.has_pharmacy_service`), not a separate dataset.
- **`Customer Sales Analysis-Misoclear and Mariprist Only.csv`** (167 rows) - already
  pre-aggregated (totals, averages, purchase interval, yearly/quarterly breakdown) by whatever
  produced it. The filename suggests this is a **product-line subset**, not the full customer
  book - treated as sample/seed data for the MVP, not assumed complete.
- **Zero customer names matched either register exactly.** Testing revealed why: many customers
  are distributors with *several* separately PPB-registered branches (e.g. "Medio-care
  Pharmaceuticals limited" corresponds to 5+ rows like "MEDIO CARE PHARMACEUTICALS - BONDO MARKET
  (Siaya)", "... - KISUMU (Kisumu)", etc.). That means matching is naturally **one customer to
  many outlet rows**, not a single foreign key - the schema (`CustomerOutletMatch` junction table)
  and the ETL (`app/etl/match_customers.py`) are both built around that from the start rather than
  bolted on later.

## Matching: what didn't work, and why

The fuzzy-matching design went through three iterations, each driven by a concrete failure found
by testing against the real data rather than by inspection alone - documented in full in
`app/etl/match_customers.py`'s module docstring, summarized here:

1. **Plain string-similarity ratio** (Python's stdlib `difflib`) was tried first and rejected -
   branch-suffix names like "... - BONDO MARKET (Siaya)" score far below a usable threshold
   against the base name.
2. **`rapidfuzz.fuzz.token_set_ratio`** handles branch suffixes well, but alone it does two wrong
   things, both confirmed against the real data: it silently scores two *different* companies that
   share only a generic word ("Fountain healthcare limited" vs "CBM HEALTHCARE LIMITED") at 90 -
   comfortably auto-confirm - and it *misses* real matches like "Philmed Pharmaceutical" vs
   "PHILMED LIMITED-UMOJA (Nairobi)" (scores only 48, since the differing tokens outweigh the one
   that actually identifies the business).
3. **The shipped design**: a distinctive-token guard. Common pharma/business words (LIMITED,
   PHARMACY, HEALTHCARE, CLINIC, HOSPITAL, ...) are stripped first; a candidate only counts as a
   match at all if at least one of the customer's *remaining* tokens appears verbatim in the outlet
   name. This is implemented as an inverted token index (candidate generation), not a filter on
   rapidfuzz's top-N results - an intermediate version that scored all ~28k outlets per customer
   and filtered the top 50 afterward still silently dropped real matches like Philmed's, because
   enough *unrelated* outlets outscored it on generic-word overlap alone before the guard ever saw
   it. Building the candidate set from the index instead guarantees every guard-passing outlet gets
   scored. A dynamic safety net (skip any token whose index bucket exceeds 300 outlets) also
   catches common words the static stoplist didn't anticipate (an early version, before this cap
   existed, matched "Sameer Park clinic" against thousands of unrelated outlets purely because
   "clinic" wasn't yet on the stoplist).

Confidence thresholds: `token_set_ratio` >= 90 -> auto-confirmed; 70-89 -> queued in the Match
Review page; below the score floor (55) or failing the guard -> not stored. On the real dataset
this produces 268 auto-confirmed matches, ~1,600 queued for review, and 39 customers (out of 167)
with no plausible match at all - largely ledger entries like "Cash sales Vincent Osino" that were
never going to correspond to a registered outlet, which is expected, not a gap to close.

## Why not further, by design

The brief explicitly asks for ML, RAG/MCP/agents, and heavier infrastructure only "to the extent to
which they are necessary" - each omission below was a decision, not an oversight, and is expanded
on in [`05-future-work.md`](05-future-work.md):

- **No ML model for churn** - the brief's own spec ("estimate churn by duration passed since last
  order") is fully satisfied by a rule (days-since-last-order normalized by the customer's own
  average purchase interval - see `app/churn.py`). There's also no labeled ground truth yet
  (confirmed lost accounts) to train a model against.
- **No RAG/agent assistant yet** - genuinely useful later, and this workspace already has two
  working patterns to build it from when the time comes (see future-work doc), but it isn't needed
  to satisfy the brief's stated requirements today.
- **No Snowflake/Databricks/Kubernetes** - unjustified at ~28k outlet rows and a 10k-user first
  year; SQLite (Postgres once real concurrent writes matter) is sufficient.
- **No live cloud deployment performed automatically** - creating free-tier accounts (Vercel,
  Render/Fly, Neon/Supabase) and connecting a GitHub repo needs the project owner's own
  credentials; see [`04-deployment.md`](04-deployment.md) for the step-by-step guide to do that
  together.
