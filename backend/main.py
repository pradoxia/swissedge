from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.health.router import router as health_router
from backend.api.marketplace.router import router as marketplace_router
from backend.api.investment.router import router as investment_router
from backend.api.observability.router import router as observability_router

app = FastAPI(
    title="SwissEdge API",
    description="Marketplace Assistant + Special Situations Investment Radar",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/health", tags=["health"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(investment_router, prefix="/api/investment", tags=["investment"])
app.include_router(observability_router, prefix="/api/observability", tags=["observability"])


@app.get("/")
async def root():
    return {"service": "SwissEdge API", "version": "0.1.0", "status": "running"}
