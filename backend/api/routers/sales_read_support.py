from __future__ import annotations

from backend.api.support.runtime_common import _dispatch_background
from backend.api.support.runtime_common import _repository_error
from backend.api.support.runtime_common import _validation_error
from backend.api.support.sales_support import _build_sales_claim_export_rows
from backend.api.support.sales_support import _build_sales_claim_overview_payload
from backend.api.support.sales_support import _get_home_bootstrap_snapshot_version
from backend.api.support.sales_support import _get_sales_claim_repository
from backend.api.support.sales_support import _get_tracker_repository
from backend.api.support.sales_support import _load_artifact_file_helpers
from backend.api.support.sales_support import _record_download_audit_log
from backend.api.support.sales_support import _resolve_sales_actor
from backend.api.support.sales_support import _sales_claim_belongs_to_actor
from backend.api.support.sales_support import _to_sales_claim_model
from backend.api.support.sales_support import _to_sales_claim_summary_user_model


def _app_module():
    from backend.api import app as app_module

    return app_module


def _build_home_bootstrap_payload(*, actor, request_id: str = ""):
    return _app_module()._build_home_bootstrap_payload(actor=actor, request_id=request_id)


def _queue_project_aggregates_cache_warm() -> None:
    _app_module()._queue_project_aggregates_cache_warm()


def _warm_default_user_tracker_export_workbook() -> None:
    _app_module()._warm_default_user_tracker_export_workbook()
