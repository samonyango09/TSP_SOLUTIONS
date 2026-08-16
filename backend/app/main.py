from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, customers, locations, matches, outlets, route_plan
from app.auth import require_session

app = FastAPI(title="TSP Solutions - Pharma Sales System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://tsp-solutions.vercel.app"],
    # Vercel gives every deploy its own preview URL (a random hash per
    # build, e.g. tsp-solutions-me5tr8uzv-tsp-pharma.vercel.app) in addition
    # to the stable production domain above - a regex covers those without
    # needing a backend redeploy every time a new preview URL is generated.
    allow_origin_regex=r"https://tsp-solutions-[a-z0-9]+-tsp-pharma\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(outlets.router, dependencies=[Depends(require_session)])
app.include_router(customers.router, dependencies=[Depends(require_session)])
app.include_router(route_plan.router, dependencies=[Depends(require_session)])
app.include_router(matches.router, dependencies=[Depends(require_session)])
app.include_router(locations.router, dependencies=[Depends(require_session)])


@app.get("/api/health")
def health():
    return {"status": "ok"}
