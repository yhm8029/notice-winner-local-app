from __future__ import annotations

from typing import Any
from typing import Protocol
from uuid import UUID

RunArtifactRow = dict[str, Any]


class ArtifactRepositoryError(RuntimeError):
    pass


class ArtifactRepositoryConfigError(ArtifactRepositoryError):
    pass


class ArtifactRepository(Protocol):
    def create_artifact(self, row: RunArtifactRow) -> RunArtifactRow: ...

    def list_artifacts(self, *, run_id: UUID) -> list[RunArtifactRow]: ...

    def get_artifact(self, artifact_id: UUID) -> RunArtifactRow | None: ...

    def delete_artifacts_for_run(self, run_id: UUID) -> int: ...
