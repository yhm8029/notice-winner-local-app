from __future__ import annotations

from fastapi import APIRouter
from fastapi import Query

from backend.api.routers.core import list_projects as core_list_projects
from backend.api.schemas import ProjectListResponse

router = APIRouter()


@router.get(
    "/api/projects",
    response_model=ProjectListResponse,
)
def list_projects(
    q: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> ProjectListResponse:
    return core_list_projects(q=q, page=page, page_size=page_size)
