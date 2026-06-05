from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Query

from backend.api.schemas import ErrorResponse
from backend.api.schemas import NoticeViewResponse
from backend.api.schemas import RelatedNoticeListResponse
from backend.api.schemas import RelatedNoticeProgressResponse
from backend.api.schemas import RelatedNoticeRecomputeResponse

router = APIRouter()


def _app_module():
    from backend.api import app as related_notice_app

    return related_notice_app


@router.get(
    "/api/projects/{project_id}/related-notices",
    response_model=RelatedNoticeListResponse,
    responses={404: {"model": ErrorResponse}},
)
def list_project_related_notices(
    project_id: UUID,
    refresh: bool = Query(default=False),
    quick: bool = Query(default=False),
) -> RelatedNoticeListResponse:
    related_notice_app = _app_module()
    return related_notice_app._list_related_notices_for_project(project_id, force_refresh=refresh, quick=quick)


@router.get(
    "/api/projects/{project_id}/related-notices/progress",
    response_model=RelatedNoticeProgressResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_project_related_notice_progress(project_id: UUID) -> RelatedNoticeProgressResponse:
    related_notice_app = _app_module()
    return related_notice_app._get_related_notice_progress_for_project(project_id)


@router.post(
    "/api/projects/{project_id}/related-notices/recompute",
    response_model=RelatedNoticeRecomputeResponse,
    responses={404: {"model": ErrorResponse}},
)
def recompute_project_related_notices(project_id: UUID) -> RelatedNoticeRecomputeResponse:
    related_notice_app = _app_module()
    return related_notice_app._force_recompute_related_notices_for_project(project_id)


@router.get(
    "/api/projects/{project_id}/notice-view",
    response_model=NoticeViewResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_project_notice_view(project_id: UUID) -> NoticeViewResponse:
    related_notice_app = _app_module()
    return NoticeViewResponse(**related_notice_app._build_project_notice_view_payload(project_id))


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
    related_notice_app = _app_module()
    notice_view_helpers = related_notice_app._load_notice_view_helpers()
    try:
        payload = notice_view_helpers["build_notice_view_payload"](
            notice_detail_url=notice_detail_url,
            notice_url=notice_url,
            project_name=project_name,
            bid_no=bid_no,
            bid_ord=bid_ord,
        )
    except ValueError as exc:
        related_notice_app._validation_error(str(exc))
    return NoticeViewResponse(**payload)
