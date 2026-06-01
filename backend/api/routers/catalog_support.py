from __future__ import annotations

from datetime import datetime
from datetime import timezone

from backend.api.support.runtime_common import _validation_error


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
