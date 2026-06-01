from __future__ import annotations

from uuid import UUID

from backend.api.support.runtime_common import ApiError
from backend.api.support.runtime_common import _validation_error


def _app_module():
    from backend.api import app as app_module

    return app_module


def _build_projects_page(*, page: int, page_size: int, q: str):
    return _app_module()._build_projects_page(page=page, page_size=page_size, q=q)


def _list_related_notices_for_project(project_id: UUID):
    return _app_module()._list_related_notices_for_project(project_id)


def _build_project_notice_view_payload(project_id: UUID) -> dict[str, object]:
    return _app_module()._build_project_notice_view_payload(project_id)


def _load_notice_view_helpers():
    return _app_module()._load_notice_view_helpers()


def _load_report_payload(report_name: str) -> dict[str, object]:
    return _app_module()._load_report_payload(report_name)
