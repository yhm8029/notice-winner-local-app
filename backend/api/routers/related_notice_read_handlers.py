from __future__ import annotations

from uuid import UUID

from backend.api.routers import app_support
from backend.api.routers import related_notice_read_support as support
from backend.api.schemas import NoticeViewResponse
from backend.api.schemas import RelatedNoticeListResponse


def list_project_related_notices(project_id: UUID) -> RelatedNoticeListResponse:
    return app_support._list_related_notices_for_project(project_id)


def get_project_notice_view(project_id: UUID) -> NoticeViewResponse:
    return NoticeViewResponse(**app_support._build_project_notice_view_payload(project_id))


def get_notice_view(
    *,
    notice_detail_url: str = "",
    notice_url: str = "",
    project_name: str = "",
    bid_no: str = "",
    bid_ord: str = "",
) -> NoticeViewResponse:
    notice_view_helpers = app_support._load_notice_view_helpers()
    try:
        payload = notice_view_helpers["build_notice_view_payload"](
            notice_detail_url=notice_detail_url,
            notice_url=notice_url,
            project_name=project_name,
            bid_no=bid_no,
            bid_ord=bid_ord,
        )
    except ValueError as exc:
        app_support._validation_error(str(exc))
    return NoticeViewResponse(**payload)
