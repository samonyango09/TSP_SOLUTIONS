# TSP Solutions - Pharma Sales System

A route-planning, prospecting, and churn-tracking tool for a pharmaceutical sales team in Kenya,
built from the brief in `TSP Solutions.docx`. Given a route ("Nairobi to Meru") it maps active,
at-risk, and churned customers along the corridor with their full sales history, plus nearby
prospective outlets (distributors, retail pharmacies, hospitals, and hospitals with an in-house
pharmacy) not yet in the customer base. It can also be browsed by outlet type/county without a
route.

Full design rationale, a code tutorial, and a deployment guide are in [`docs/`](docs/) - start
with [`docs/00-discovery-and-design.md`](docs/00-discovery-and-design.md).

## Architecture

- **backend/** - Python/FastAPI + SQLModel/SQLite. An ETL pipeline (`app/etl/`) loads the PPB
  pharmaceutical-outlet register and the KMHFR hospital register, fuzzy-matches the customer sales
  CSV to those registers, and derives town/county centroids for the route planner's search.
- **frontend/** - React + Vite + TypeScript + Tailwind + Leaflet.

## Setup

### Data

The two outlet-register CSVs live in `data/raw/` (copied once from
`../Clean Data and Analysis/`, gitignored - see [`docs/00-discovery-and-design.md`](docs/00-discovery-and-design.md)
for why). If they're missing, re-copy them:

```bash
cp "../Clean Data and Analysis/Geocoded Registered Pharmaceutical Outlets in Kenya.csv" data/raw/geocoded_pharmaceutical_outlets.csv
cp "../Clean Data and Analysis/Registered Hospitals in Kenya.csv" data/raw/registered_hospitals.csv
```

### Backend

```bash
cd backend
py -3.13 -m venv .venv
./.venv/Scripts/pip install -r requirements.txt

cp .env.example .env   # optional: set APP_PASSWORD to require login

./.venv/Scripts/python -m app.etl.run_all   # loads outlets + customers, runs matching
./.venv/Scripts/python -m pytest
./.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Using it

1. **Route Planner** - enter a from/to town or county and a corridor width; see active, at-risk,
   and churned customers plus prospective outlets along that path, each with its sales history and
   distance from the route.
2. **Prospecting** - browse outlets by type (distributor, retail pharmacy, hospital, hospital with
   pharmacy) and county without a route.
3. **Match Review** - the fuzzy customer-to-outlet name matching auto-confirms high-confidence
   matches and queues everything else here for a human to confirm or reject.
4. Click a customer to see its full yearly/quarterly sales history and matched outlet(s).
