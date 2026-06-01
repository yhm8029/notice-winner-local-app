from __future__ import annotations

from uuid import UUID
from uuid import uuid4

from backend.phase1_defaults import load_phase1_identity

from .artifacts import ArtifactRepository
from .artifacts import ArtifactRepositoryConfigError
from .artifacts import RunArtifactRow
from .sqlite_common import LocalRowsStore
from .sqlite_common import SqliteRepositoryConfig
from .sqlite_common import row_sort_text
from .sqlite_common import utc_now_text

TABLE_NAME = "run_artifacts"


class SqliteArtifactRepository(ArtifactRepository):
    def __init__(self, config: SqliteRepositoryConfig | None = None) -> None:
        self._store = LocalRowsStore(config or SqliteRepositoryConfig.from_env(error_cls=ArtifactRepositoryConfigError))
        self._organization_id = str(load_phase1_identity().organization_id)

    def create_artifact(self, row: RunArtifactRow) -> RunArtifactRow:
        artifact_id = str(row.get("id") or uuid4())
        stored: RunArtifactRow = {
            "id": artifact_id,
            **row,
            "run_id": str(row.get("run_id")),
            "created_at": row.get("created_at") or utc_now_text(),
            "meta_json": dict(row.get("meta_json") or {}),
        }
        stored["id"] = artifact_id
        return self._store.upsert_row(
            TABLE_NAME,
            artifact_id,
            stored,
            created_at=stored.get("created_at"),
        )

    def list_artifacts(self, *, run_id: UUID) -> list[RunArtifactRow]:
        rows = [
            _normalize_artifact(row)
            for row in self._store.list_rows(TABLE_NAME)
            if str(row.get("run_id")) == str(run_id)
            and self._is_local_organization(row)
        ]
        rows.sort(key=lambda item: row_sort_text(item.get("created_at")), reverse=True)
        return rows

    def get_artifact(self, artifact_id: UUID) -> RunArtifactRow | None:
        row = self._store.get_row(TABLE_NAME, str(artifact_id))
        if row is None or not self._is_local_organization(row):
            return None
        return _normalize_artifact(row)

    def delete_artifacts_for_run(self, run_id: UUID) -> int:
        return self._store.delete_matching(
            TABLE_NAME,
            lambda row: str(row.get("run_id")) == str(run_id) and self._is_local_organization(row),
        )

    def _is_local_organization(self, row: dict[str, object]) -> bool:
        return str(row.get("organization_id")) == self._organization_id


def _normalize_artifact(row: dict[str, object]) -> RunArtifactRow:
    normalized = dict(row)
    normalized["meta_json"] = dict(normalized.get("meta_json") or {})
    return normalized
