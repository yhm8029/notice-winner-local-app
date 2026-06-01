from __future__ import annotations

import threading
from typing import Any

from fastapi import status

from backend.repositories import ArtifactRepositoryConfigError
from backend.repositories import DownloadAuditLogRepositoryError
from backend.repositories import BackfillConflictRepositoryConfigError
from backend.repositories import get_artifact_repository
from backend.repositories import get_backfill_conflict_repository
from backend.repositories import get_download_audit_log_repository
from backend.repositories import get_run_log_repository
from backend.repositories import get_run_repository
from backend.repositories import get_sales_claim_repository
from backend.repositories import get_tracker_change_event_repository
from backend.repositories import get_tracker_entry_repository
from backend.repositories.factory import get_login_audit_log_repository
from backend.repositories.login_audit_logs import LoginAuditLogRepositoryError
from backend.repositories import RunLogRepositoryConfigError
from backend.repositories import RunRepositoryConfigError
from backend.repositories import SalesClaimRepositoryConfigError
from backend.repositories import TrackerChangeEventRepositoryConfigError
from backend.repositories import TrackerEntryRepositoryConfigError


class ApiError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


class _BackendApiAppProxy:
    def __getattr__(self, name: str) -> Any:
        from backend.api import app as app_module

        return getattr(app_module, name)


_backend_api_app = _BackendApiAppProxy()


def _validation_error(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="validation_error",
        message=message,
    )


def _not_found(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_404_NOT_FOUND,
        code="not_found",
        message=message,
    )


def _repository_error(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="repository_error",
        message=message,
    )


def _conflict_error(message: str) -> None:
    raise ApiError(
        status_code=status.HTTP_409_CONFLICT,
        code="conflict",
        message=message,
    )


def _dispatch_background(target: Any, *args: Any, **kwargs: Any) -> None:
    worker = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    worker.start()


def _get_run_repository():
    try:
        return get_run_repository()
    except RunRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_artifact_repository():
    try:
        return get_artifact_repository()
    except ArtifactRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_run_log_repository():
    try:
        return get_run_log_repository()
    except RunLogRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_tracker_repository():
    try:
        return get_tracker_entry_repository()
    except TrackerEntryRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_sales_claim_repository():
    try:
        return get_sales_claim_repository()
    except SalesClaimRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_download_audit_log_repository():
    try:
        return get_download_audit_log_repository()
    except DownloadAuditLogRepositoryError as exc:
        _repository_error(str(exc))


def _get_tracker_change_event_repository():
    try:
        return get_tracker_change_event_repository()
    except TrackerChangeEventRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_backfill_conflict_repository():
    try:
        return get_backfill_conflict_repository()
    except BackfillConflictRepositoryConfigError as exc:
        _repository_error(str(exc))


def _get_login_audit_log_repository():
    try:
        return get_login_audit_log_repository()
    except LoginAuditLogRepositoryError as exc:
        _repository_error(str(exc))
