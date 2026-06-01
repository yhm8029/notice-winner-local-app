from __future__ import annotations

from backend.api.auth_runtime import append_audit_log as _append_audit_log
from backend.api.auth_runtime import AuthRuntimeError
from backend.api.support.runtime_common import _repository_error
from backend.api.support.runtime_common import _validation_error
from backend.api.support.sales_support import _get_sales_claim_repository
from backend.api.support.sales_support import _resolve_sales_actor
from backend.api.support.sales_support import _resolve_transfer_target_user
from backend.api.support.sales_support import _to_sales_claim_model


def _get_auth_runtime_error():
    return AuthRuntimeError


def _invalidate_sales_overview_cache(*, organization_id):
    from backend.api.support.sales_support import _invalidate_sales_overview_cache as support_invalidate_sales_overview_cache

    support_invalidate_sales_overview_cache(organization_id=organization_id)
