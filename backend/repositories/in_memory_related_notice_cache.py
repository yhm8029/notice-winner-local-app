from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import uuid4

from backend.phase1_defaults import DEFAULT_PHASE1_ORGANIZATION_ID

from .related_notice_cache import RelatedNoticeCacheRepository
from .related_notice_cache import RelatedNoticeCacheRow


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryRelatedNoticeCacheRepository(RelatedNoticeCacheRepository):
    def __init__(self) -> None:
        self._rows_by_project_key: dict[tuple[str, str], RelatedNoticeCacheRow] = {}

    def get_cache(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        key = str(project_key or "").strip()
        if not key:
            return None
        snapshot_key = str(snapshot_set_id or "legacy").strip() or "legacy"
        row = self._rows_by_project_key.get((key, snapshot_key))
        return dict(row) if row is not None else None

    def upsert_cache(self, row: RelatedNoticeCacheRow) -> RelatedNoticeCacheRow:
        project_key = str(row.get("project_key") or "").strip()
        snapshot_set_id = str(row.get("snapshot_set_id") or "legacy").strip() or "legacy"
        now = _utc_now_iso()
        existing = dict(self._rows_by_project_key.get((project_key, snapshot_set_id)) or {})
        merged = {
            "id": existing.get("id") or str(uuid4()),
            "organization_id": existing.get("organization_id") or str(DEFAULT_PHASE1_ORGANIZATION_ID),
            "project_key": project_key,
            "snapshot_set_id": snapshot_set_id,
            "project_name": "",
            "project_search_name": "",
            "issuer_name": "",
            "status": "queued",
            "source": "",
            "algorithm_version": 0,
            "item_count": 0,
            "error": "",
            "payload_json": {},
            "source_run_id": None,
            "generated_at": None,
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
        }
        merged.update(existing)
        merged.update(dict(row))
        merged["project_key"] = project_key
        merged["snapshot_set_id"] = snapshot_set_id
        merged["updated_at"] = now
        self._rows_by_project_key[(project_key, snapshot_set_id)] = dict(merged)
        return dict(merged)

    def list_queued(self, *, limit: int = 5) -> list[RelatedNoticeCacheRow]:
        rows = [
            dict(row)
            for row in self._rows_by_project_key.values()
            if str(row.get("status") or "").strip() == "queued"
        ]
        rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""))
        return rows[: max(0, int(limit or 0))]

    def claim_queued(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        key = str(project_key or "").strip()
        snapshot_key = str(snapshot_set_id or "legacy").strip() or "legacy"
        row_key = (key, snapshot_key)
        row = dict(self._rows_by_project_key.get(row_key) or {})
        if not row or str(row.get("status") or "").strip() != "queued":
            return None
        row["status"] = "running"
        row["updated_at"] = _utc_now_iso()
        self._rows_by_project_key[row_key] = dict(row)
        return dict(row)
