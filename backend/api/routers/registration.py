from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routers.admin import router as admin_router
from backend.api.routers.artifacts import router as artifacts_router
from backend.api.routers.auth import router as auth_router
from backend.api.routers.backfill_conflicts import router as backfill_conflicts_router
from backend.api.routers.core import router as core_router
from backend.api.routers.reports import router as reports_router
from backend.api.routers.runs import router as runs_router
from backend.api.routers.sales_claims import router as sales_claims_router
from backend.api.routers.tracker_admin import router as tracker_admin_router
from backend.api.routers.tracker import router as tracker_router

_ROUTERS = (
    auth_router,
    artifacts_router,
    admin_router,
    backfill_conflicts_router,
    core_router,
    sales_claims_router,
    reports_router,
    runs_router,
    tracker_admin_router,
    tracker_router,
)


def register_routes(app: FastAPI, *, frontend_dir: Path) -> None:
    for router in _ROUTERS:
        app.include_router(router)
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    app.mount("/", StaticFiles(directory=frontend_dir), name="frontend_assets")
