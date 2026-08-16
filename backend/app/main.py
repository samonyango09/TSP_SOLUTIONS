from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, customers, locations, matches, outlets, route_plan
from app.auth import require_session

app = FastAPI(title="TSP Solutions - Pharma Sales System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
