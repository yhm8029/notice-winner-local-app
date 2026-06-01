from __future__ import annotations

from backend.api.support.runtime_common import _get_backfill_conflict_repository as get_backfill_conflict_repository
from backend.api.support.runtime_common import _get_tracker_repository
from backend.api.support.runtime_common import _not_found
from backend.api.support.runtime_common import _repository_error
from backend.api.support.runtime_common import _validation_error
from backend.api.support.sales_support import _resolve_sales_actor
from backend.api.support.tracker_support import BACKFILL_CONFLICT_RESOLUTIONS
from backend.api.support.tracker_support import _resolve_request_organization_id
from backend.api.support.tracker_support import _to_backfill_conflict_model


def get_backfill_conflict_resolutions():
    return BACKFILL_CONFLICT_RESOLUTIONS
