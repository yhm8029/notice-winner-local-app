# Artifact Read Backend Seam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract artifact read/response shaping helpers from `backend/api/app.py` into a focused backend service module without changing API behavior for artifact listing, downloading, or previewing.

**Architecture:** Introduce a dedicated backend seam for artifact read logic, keeping FastAPI routes in `backend/api/app.py` thin. The new service module should own artifact item shaping, artifact file-path resolution helpers, and preview payload orchestration, while the route layer keeps repository lookup, visibility checks, and HTTP error translation.

**Tech Stack:** Python, FastAPI, unittest, repository-backed artifact metadata, filesystem artifact storage

---

### Task 1: Lock Artifact Read Behavior With Service Tests

**Files:**
- Create: `backend/services/artifact_read_backend.py`
- Create: `tests/test_artifact_read_backend.py`
- Modify: `backend/api/app.py`
- Test: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write the failing service tests**

```python
import unittest
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.services.artifact_read_backend import build_artifact_item_payload


class ArtifactReadBackendTests(unittest.TestCase):
    def test_build_artifact_item_payload_includes_download_url_and_meta_defaults(self) -> None:
        artifact_id = uuid4()
        payload = build_artifact_item_payload(
            row={
                "id": artifact_id,
                "artifact_type": "winner_csv",
                "file_name": "winner.csv",
                "mime_type": "text/csv",
                "size_bytes": None,
                "checksum": None,
                "meta_json": None,
                "created_at": datetime(2026, 3, 30, tzinfo=timezone.utc),
            },
            build_download_url=lambda current_id: f"/api/artifacts/{current_id}/download",
        )

        self.assertEqual(payload["artifact_type"], "winner_csv")
        self.assertEqual(payload["download_url"], f"/api/artifacts/{artifact_id}/download")
        self.assertEqual(payload["size_bytes"], 0)
        self.assertEqual(payload["meta"], {})
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `python -m unittest tests.test_artifact_read_backend`
Expected: FAIL because `backend.services.artifact_read_backend` or `build_artifact_item_payload` does not exist yet.

- [ ] **Step 3: Add a second test for preview orchestration**

```python
from backend.services.artifact_read_backend import build_artifact_preview_payload_for_row

    def test_build_artifact_preview_payload_for_row_delegates_to_preview_builder(self) -> None:
        messages = []
        result = build_artifact_preview_payload_for_row(
            row={
                "artifact_type": "tracking_excel",
                "storage_path": "output/artifacts/run/project_tracking.xlsx",
            },
            resolve_artifact_path_fn=lambda storage_path: Path("/tmp") / Path(storage_path).name,
            build_preview_payload_fn=lambda **kwargs: {
                "artifact_type": kwargs["artifact_type"],
                "path_name": kwargs["file_path"].name,
                "limit": kwargs["limit"],
            },
            limit=5,
        )

        self.assertEqual(
            result,
            {"artifact_type": "tracking_excel", "path_name": "project_tracking.xlsx", "limit": 5},
        )
```

- [ ] **Step 4: Run tests again to verify the full red state**

Run: `python -m unittest tests.test_artifact_read_backend`
Expected: FAIL on missing implementation, with no unrelated import or syntax failures.

- [ ] **Step 5: Commit**

```bash
git add tests/test_artifact_read_backend.py
git commit -m "test: add artifact read backend coverage"
```

### Task 2: Implement The Artifact Read Backend Seam

**Files:**
- Create: `backend/services/artifact_read_backend.py`
- Modify: `backend/api/app.py`
- Test: `tests/test_artifact_read_backend.py`

- [ ] **Step 1: Implement pure artifact item shaping**

```python
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from uuid import UUID


def build_artifact_item_payload(*, row: dict[str, Any], build_download_url: Callable[[str], str]) -> dict[str, Any]:
    artifact_id = str(row["id"])
    return {
        "id": UUID(artifact_id),
        "artifact_type": str(row["artifact_type"]),
        "file_name": str(row["file_name"]),
        "mime_type": str(row["mime_type"]),
        "size_bytes": int(row.get("size_bytes") or 0),
        "checksum": str(row.get("checksum") or ""),
        "meta": dict(row.get("meta_json") or {}),
        "download_url": build_download_url(artifact_id),
        "download_url_expires_in": 600,
        "created_at": row["created_at"],
    }
```

- [ ] **Step 2: Implement preview-path orchestration helper**

```python
def build_artifact_preview_payload_for_row(
    *,
    row: dict[str, Any],
    resolve_artifact_path_fn: Callable[[str], Path],
    build_preview_payload_fn: Callable[..., dict[str, Any]],
    limit: int,
) -> dict[str, Any]:
    storage_path = str(row.get("storage_path") or "").strip()
    file_path = resolve_artifact_path_fn(storage_path)
    return build_preview_payload_fn(
        artifact_type=str(row["artifact_type"]),
        file_path=file_path,
        limit=limit,
    )
```

- [ ] **Step 3: Rewire `backend/api/app.py` to use the new backend module**

```python
from backend.services.artifact_read_backend import (
    build_artifact_item_payload as _build_artifact_item_payload_impl,
)
from backend.services.artifact_read_backend import (
    build_artifact_preview_payload_for_row as _build_artifact_preview_payload_for_row_impl,
)


def _to_artifact_item(request: Request, row: dict[str, Any]) -> ArtifactItem:
    return ArtifactItem(
        **_build_artifact_item_payload_impl(
            row=row,
            build_download_url=lambda artifact_id: str(
                request.url_for("download_artifact", artifact_id=artifact_id)
            ),
        )
    )
```

- [ ] **Step 4: Run the focused service suite**

Run: `python -m unittest tests.test_artifact_read_backend tests.test_artifact_preview_backend`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/artifact_read_backend.py backend/api/app.py tests/test_artifact_read_backend.py
git commit -m "refactor: extract artifact read backend seam"
```

### Task 3: Verify API Behavior Stays Stable

**Files:**
- Modify: `tests/api/test_phase1_api.py`
- Modify: `backend/api/app.py`
- Test: `tests/test_artifact_read_backend.py`
- Test: `tests/test_artifact_preview_backend.py`

- [ ] **Step 1: Add one API-level assertion that artifact list items still expose the download URL contract**

```python
self.assertEqual(artifacts_status, 200)
artifact = artifacts_payload["items"][0]
self.assertIn("/api/artifacts/", artifact["download_url"])
self.assertEqual(artifact["download_url_expires_in"], 600)
self.assertIn("meta", artifact)
```

- [ ] **Step 2: Add one API-level assertion that previewing still returns the same artifact type**

```python
preview_status, preview_payload = server.request_json(
    "GET",
    f"/api/artifacts/{artifact['id']}/preview?limit=5",
)
self.assertEqual(preview_status, 200)
self.assertEqual(preview_payload["artifact_type"], "tracking_excel")
```

- [ ] **Step 3: Run the targeted backend verification**

Run: `python -m unittest tests.test_artifact_read_backend tests.test_artifact_preview_backend tests.api.test_phase1_api`
Expected: PASS

- [ ] **Step 4: Verify the worktree**

Run: `git status --short`
Expected: only the intended backend files are modified before commit, then clean after commit

- [ ] **Step 5: Commit final backend test coverage**

```bash
git add backend/api/app.py backend/services/artifact_read_backend.py tests/test_artifact_read_backend.py tests/api/test_phase1_api.py
git commit -m "test: cover artifact read api seam"
```
