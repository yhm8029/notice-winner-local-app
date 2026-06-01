from __future__ import annotations

from backend.repositories import RelatedNoticeCacheRepositoryConfigError
from backend.repositories import get_related_notice_cache_repository

from backend.api.support.runtime_common import _get_login_audit_log_repository
from backend.api.support.runtime_common import _repository_error
from backend.api.support.tracker_read_support import _get_tracker_entry_snapshot_repository


def _get_related_notice_cache_repository():
    try:
        return get_related_notice_cache_repository()
    except RelatedNoticeCacheRepositoryConfigError as exc:
        _repository_error(str(exc))
