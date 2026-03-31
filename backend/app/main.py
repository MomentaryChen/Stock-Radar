from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.routers import (
    accuracy,
    alerts,
    backtest,
    charts,
    forecast,
    industries,
    news,
    scores,
    technical,
    usage,
    watchlists,
)
from backend.app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Stock Radar API",
    description="台股量化評分 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scores.router, prefix="/api/v1")
app.include_router(technical.router, prefix="/api/v1")
app.include_router(forecast.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(charts.router, prefix="/api/v1")
app.include_router(watchlists.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(industries.router, prefix="/api/v1")
app.include_router(accuracy.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(usage.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
