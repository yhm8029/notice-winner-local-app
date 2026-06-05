from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query

from backend.api.routers.core import list_projects as core_list_projects
from backend.api.routers.related_notice import get_notice_view as related_notice_get_notice_view
from backend.api.routers.related_notice import get_project_notice_view as related_notice_get_project_notice_view
from backend.api.routers.related_notice import list_project_related_notices as related_notice_list_project_related_notices
from backend.api.schemas import ErrorResponse
from backend.api.schemas import NoticeViewResponse
from backend.api.schemas import ProjectListResponse
from backend.api.schemas import RelatedNoticeListResponse

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


@router.get(
    "/api/projects/{project_id}/related-notices",
    response_model=RelatedNoticeListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_project_related_notices(project_id: UUID) -> RelatedNoticeListResponse:
    return related_notice_list_project_related_notices(project_id)


@router.get(
    "/api/projects/{project_id}/notice-view",
    response_model=NoticeViewResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_project_notice_view(project_id: UUID) -> NoticeViewResponse:
    return related_notice_get_project_notice_view(project_id)


@router.get(
    "/api/notices/view",
    response_model=NoticeViewResponse,
    responses={400: {"model": ErrorResponse}},
)
def get_notice_view(
    notice_detail_url: str = "",
    notice_url: str = "",
    project_name: str = "",
    bid_no: str = "",
    bid_ord: str = "",
) -> NoticeViewResponse:
    return related_notice_get_notice_view(
        notice_detail_url=notice_detail_url,
        notice_url=notice_url,
        project_name=project_name,
        bid_no=bid_no,
        bid_ord=bid_ord,
    )
