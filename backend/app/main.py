from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, customers, locations, matches, outlets, route_plan
from app.auth import require_session

app = FastAPI(title="TSP Solutions - Pharma Sales System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tsp-solutions.vercel.app"],
    # Two things a plain allow_origins list can't express, covered by regex:
    # - Vite falls back to the next free port (5174, 5175, ...) if 5173 is
    #   already taken by another local process, so local dev origins are
    #   matched by port range rather than one hardcoded port.
    # - Vercel gives every deploy its own preview URL (a random hash per
    #   build, e.g. tsp-solutions-me5tr8uzv-tsp-pharma.vercel.app) in
    #   addition to the stable production domain above.
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):517\d|https://tsp-solutions-[a-z0-9]+-tsp-pharma\.vercel\.app",
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
