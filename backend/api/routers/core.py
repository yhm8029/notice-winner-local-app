from __future__ import annotations

from fastapi import APIRouter
from fastapi import Query

from backend.api.schemas import DashboardSummaryResponse
from backend.api.schemas import ProjectListResponse

router = APIRouter()


def _app_module():
    from backend.api import app as core_app

    return core_app


@router.get(
    "/api/dashboard/summary",
    response_model=DashboardSummaryResponse,
)
def get_dashboard_summary() -> DashboardSummaryResponse:
    core_app = _app_module()
    return core_app._get_cached_dashboard_summary()


@router.get(
    "/api/projects",
    response_model=ProjectListResponse,
)
def list_projects(
    q: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> ProjectListResponse:
    core_app = _app_module()
    items, total = core_app._build_projects_page(page=page, page_size=page_size, q=q.strip())
    return ProjectListResponse(items=items, page=page, page_size=page_size, total=total)
