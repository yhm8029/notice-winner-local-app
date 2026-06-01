from __future__ import annotations

from datetime import datetime
from datetime import timezone
from uuid import UUID
from uuid import uuid4

from .artifacts import ArtifactRepository
from .artifacts import RunArtifactRow


class InMemoryArtifactRepository(ArtifactRepository):
    def __init__(self) -> None:
        self._artifacts: dict[UUID, RunArtifactRow] = {}

    def create_artifact(self, row: RunArtifactRow) -> RunArtifactRow:
        artifact_id = uuid4()
        created_at = datetime.now(timezone.utc)
        stored: RunArtifactRow = {
            "id": artifact_id,
            **row,
            "run_id": _to_uuid(row.get("run_id")),
            "created_at": created_at,
        }
        self._artifacts[artifact_id] = stored
        return dict(stored)

    def list_artifacts(self, *, run_id: UUID) -> list[RunArtifactRow]:
        rows = [dict(row) for row in self._artifacts.values() if row["run_id"] == run_id]
        rows.sort(key=lambda item: item["created_at"], reverse=True)
        return rows

    def get_artifact(self, artifact_id: UUID) -> RunArtifactRow | None:
        row = self._artifacts.get(artifact_id)
        if row is None:
            return None
        return dict(row)

    def delete_artifacts_for_run(self, run_id: UUID) -> int:
        matching_ids = [artifact_id for artifact_id, row in self._artifacts.items() if row["run_id"] == run_id]
        for artifact_id in matching_ids:
            self._artifacts.pop(artifact_id, None)
        return len(matching_ids)


def _to_uuid(value: object) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))
