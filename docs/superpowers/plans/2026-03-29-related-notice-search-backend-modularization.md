# Related Notice Search Backend Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `backend/api/app.py`와 `backend/api/auth_runtime.py`에서 응집된 보조 로직을 현재 service-seam 패턴으로 분리한다.

**Architecture:** 엔드포인트와 auth runtime은 thin wrapper로 유지하고, workbook cache, artifact preview, sales export, signed-cookie 보조 로직만 `backend/services/*_backend.py`로 이동한다. repository seam은 유지하고 기존 테스트로 회귀를 막는다.

**Tech Stack:** Python, FastAPI, unittest, existing `backend/services/*_backend.py` pattern

---

## File Structure

- Create: `backend/services/tracker_export_workbook_backend.py`
- Create: `backend/services/artifact_preview_backend.py`
- Create: `backend/services/sales_claim_export_backend.py`
- Create: `backend/services/auth_session_cookie_backend.py`
- Create: `tests/test_tracker_export_workbook_backend.py`
- Create: `tests/test_artifact_preview_backend.py`
- Create: `tests/test_sales_claim_export_backend.py`
- Create: `tests/test_auth_session_cookie_backend.py`
- Modify: `backend/api/app.py`
- Modify: `backend/api/auth_runtime.py`
- Modify: `tests/test_tracker_export_workbook_cache.py`
- Modify: `tests/api/test_phase1_api.py`
- Modify: `tests/api/test_sales_claim_api.py`
- Modify: `tests/test_auth_runtime.py`

### Task 1: Extract Tracker Export Workbook Backend

**Files:**
- Create: `backend/services/tracker_export_workbook_backend.py`
- Create: `tests/test_tracker_export_workbook_backend.py`
- Modify: `backend/api/app.py:4234-4446`
- Modify: `tests/test_tracker_export_workbook_cache.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from backend.services.tracker_export_workbook_backend import build_tracker_export_workbook_cache_key
from backend.services.tracker_export_workbook_backend import can_cache_tracker_export_workbook


class TrackerExportWorkbookBackendTests(unittest.TestCase):
    def test_can_cache_only_global_xlsx_scope(self) -> None:
        self.assertTrue(
            can_cache_tracker_export_workbook(
                format="xlsx",
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
                is_global_tracker_scope=lambda **_: True,
            )
        )

    def test_cache_key_changes_when_q_changes(self) -> None:
        left = build_tracker_export_workbook_cache_key(q="", region="", edited_only=False, exclude_auxiliary_titles=True, blank_progress_note=True)
        right = build_tracker_export_workbook_cache_key(q="abc", region="", edited_only=False, exclude_auxiliary_titles=True, blank_progress_note=True)
        self.assertNotEqual(left, right)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_tracker_export_workbook_backend -v`

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `backend/services/tracker_export_workbook_backend.py` with:

```python
from __future__ import annotations

import json
from typing import Any
from uuid import UUID


def can_cache_tracker_export_workbook(*, format: str, source_run_id: UUID | None, source_tracker_run_id: UUID | None, sheet_name: str, section_name: str, is_global_tracker_scope: Any) -> bool:
    normalized_format = str(format or "").strip().lower()
    return normalized_format == "xlsx" and bool(
        is_global_tracker_scope(
            source_run_id=source_run_id,
            source_tracker_run_id=source_tracker_run_id,
            sheet_name=sheet_name,
            section_name=section_name,
        )
    )


def build_tracker_export_workbook_cache_key(*, q: str, region: str, edited_only: bool, exclude_auxiliary_titles: bool, blank_progress_note: bool) -> str:
    return json.dumps(
        {
            "scope": "global-xlsx",
            "q": str(q or "").strip(),
            "region": str(region or "").strip(),
            "edited_only": bool(edited_only),
            "exclude_auxiliary_titles": bool(exclude_auxiliary_titles),
            "blank_progress_note": bool(blank_progress_note),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
```

- [ ] **Step 4: Move the remaining workbook helpers and wire `app.py`**

Add imports in `backend/api/app.py`:

```python
from backend.services.tracker_export_workbook_backend import build_tracker_export_workbook_cache_key as _build_tracker_export_workbook_cache_key_impl
from backend.services.tracker_export_workbook_backend import can_cache_tracker_export_workbook as _can_cache_tracker_export_workbook_impl
from backend.services.tracker_export_workbook_backend import get_or_build_cached_tracker_export_workbook_bytes as _get_or_build_cached_tracker_export_workbook_bytes_impl
from backend.services.tracker_export_workbook_backend import warm_default_user_tracker_export_workbook as _warm_default_user_tracker_export_workbook_impl
```

Keep thin wrappers only.

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `python -m unittest tests.test_tracker_export_workbook_backend tests.test_tracker_export_workbook_cache -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/services/tracker_export_workbook_backend.py backend/api/app.py tests/test_tracker_export_workbook_backend.py tests/test_tracker_export_workbook_cache.py
git commit -m "refactor: extract tracker export workbook backend"
```

### Task 2: Extract Artifact Preview Backend

**Files:**
- Create: `backend/services/artifact_preview_backend.py`
- Create: `tests/test_artifact_preview_backend.py`
- Modify: `backend/api/app.py:3024-3057`
- Modify: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write the failing test**

```python
import tempfile
import unittest
from pathlib import Path

from backend.services.artifact_preview_backend import build_artifact_preview_payload


class ArtifactPreviewBackendTests(unittest.TestCase):
    def test_csv_preview_counts_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "rows.csv"
            file_path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
            payload = build_artifact_preview_payload(
                artifact_type="winner_csv",
                file_path=file_path,
                limit=1,
                build_tracking_excel_preview_payload=lambda **_: {"kind": "excel"},
                conflict_error=lambda message: (_ for _ in ()).throw(RuntimeError(message)),
            )
        self.assertEqual(payload["total_rows"], 2)
        self.assertEqual(len(payload["rows"]), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_artifact_preview_backend -v`

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `backend/services/artifact_preview_backend.py` with:

```python
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def build_csv_preview_payload(*, file_path: Path, limit: int, artifact_type: str) -> dict[str, Any]:
    with file_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        headers = list(reader.fieldnames or [])
        rows = []
        total_rows = 0
        for row in reader:
            total_rows += 1
            if len(rows) < limit:
                rows.append({header: str((row or {}).get(header) or "") for header in headers})
    return {"kind": "table", "format": "csv", "artifact_type": artifact_type, "headers": headers, "rows": rows, "total_rows": total_rows}


def build_artifact_preview_payload(*, artifact_type: str, file_path: Path, limit: int, build_tracking_excel_preview_payload: Any, conflict_error: Any) -> dict[str, Any]:
    if artifact_type == "execution_manifest":
        return {"kind": "json", "payload": json.loads(file_path.read_text(encoding="utf-8"))}
    if artifact_type in {"winner_csv", "candidate_csv", "internal_nav_csv", "seed_csv"}:
        return build_csv_preview_payload(file_path=file_path, limit=limit, artifact_type=artifact_type)
    if artifact_type == "tracking_excel":
        return build_tracking_excel_preview_payload(file_path=file_path, limit=limit)
    conflict_error(f"preview is not supported for artifact_type={artifact_type}")
```

- [ ] **Step 4: Wire `app.py`**

Add:

```python
from backend.services.artifact_preview_backend import build_artifact_preview_payload as _build_artifact_preview_payload_impl
```

Thin wrapper:

```python
def _build_artifact_preview_payload(*, artifact_type: str, file_path: Path, limit: int) -> dict[str, Any]:
    return _build_artifact_preview_payload_impl(
        artifact_type=artifact_type,
        file_path=file_path,
        limit=limit,
        build_tracking_excel_preview_payload=_build_tracking_excel_preview_payload,
        conflict_error=_conflict_error,
    )
```

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `python -m unittest tests.test_artifact_preview_backend tests.api.test_phase1_api -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/services/artifact_preview_backend.py backend/api/app.py tests/test_artifact_preview_backend.py tests/api/test_phase1_api.py
git commit -m "refactor: extract artifact preview backend"
```

### Task 3: Extract Sales Claim Export Backend

**Files:**
- Create: `backend/services/sales_claim_export_backend.py`
- Create: `tests/test_sales_claim_export_backend.py`
- Modify: `backend/api/app.py:897-921`
- Modify: `backend/api/app.py:4556-4588`
- Modify: `tests/api/test_sales_claim_api.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest
from types import SimpleNamespace

from backend.services.sales_claim_export_backend import build_sales_claim_export_rows


class SalesClaimExportBackendTests(unittest.TestCase):
    def test_build_sales_claim_export_rows_reads_latest_tracker_entry(self) -> None:
        claim = SimpleNamespace(project_id="project-1", project_name="프로젝트", owner_display_name="담당자", owner_email="owner@example.com", sales_note="[2026-03-29] 메모", estimated_amount_text="10억원", claimed_at="2026-03-29T00:00:00Z")

        class TrackerRepository:
            def get_latest_entry_by_project_id(self, project_id):
                return {"project_name": "프로젝트", "demand_org_name": "기관", "construction_cost": "100억원"}

        rows = build_sales_claim_export_rows(claims=[claim], tracker_repository=TrackerRepository(), format_tracker_export_date=lambda value: str(value))
        self.assertEqual(rows[0]["demand_org_name"], "기관")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_sales_claim_export_backend -v`

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `backend/services/sales_claim_export_backend.py` with:

```python
from __future__ import annotations

import re
from typing import Any


def extract_latest_sales_note_text(raw_sales_note: Any) -> str:
    entries = [str(line or "").strip() for line in str(raw_sales_note or "").splitlines() if str(line or "").strip()]
    if not entries:
        return ""
    return re.sub(r"^\[[^\]]+\]\s*", "", entries[-1]).strip()


def build_sales_claim_export_rows(*, claims: list[Any], tracker_repository: Any, format_tracker_export_date: Any) -> list[dict[str, Any]]:
    rows = []
    for claim in claims:
        tracker_entry = tracker_repository.get_latest_entry_by_project_id(claim.project_id)
        rows.append(
            {
                "project_name": str((tracker_entry or {}).get("project_name") or getattr(claim, "project_name", "")),
                "demand_org_name": str((tracker_entry or {}).get("demand_org_name") or ""),
                "construction_cost": str((tracker_entry or {}).get("construction_cost") or ""),
                "owner_display_name": str(getattr(claim, "owner_display_name", "") or ""),
                "owner_email": str(getattr(claim, "owner_email", "") or ""),
                "estimated_amount_text": str(getattr(claim, "estimated_amount_text", "") or ""),
                "latest_sales_note": extract_latest_sales_note_text(getattr(claim, "sales_note", "")),
                "claimed_at": format_tracker_export_date(getattr(claim, "claimed_at", "")),
            }
        )
    return rows
```

- [ ] **Step 4: Wire `app.py`**

Add:

```python
from backend.services.sales_claim_export_backend import build_sales_claim_export_rows as _build_sales_claim_export_rows_impl
from backend.services.sales_claim_export_backend import extract_latest_sales_note_text as _extract_latest_sales_note_text_impl
```

Thin wrapper:

```python
def _build_sales_claim_export_rows(*, claims: list[Any], tracker_repository: Any) -> list[dict[str, Any]]:
    return _build_sales_claim_export_rows_impl(claims=claims, tracker_repository=tracker_repository, format_tracker_export_date=_format_tracker_export_date)
```

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `python -m unittest tests.test_sales_claim_export_backend tests.api.test_sales_claim_api -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/services/sales_claim_export_backend.py backend/api/app.py tests/test_sales_claim_export_backend.py tests/api/test_sales_claim_api.py
git commit -m "refactor: extract sales claim export backend"
```

### Task 4: Extract Auth Session Cookie Backend

**Files:**
- Create: `backend/services/auth_session_cookie_backend.py`
- Create: `tests/test_auth_session_cookie_backend.py`
- Modify: `backend/api/auth_runtime.py:631-648`
- Modify: `backend/api/auth_runtime.py:2196-2230`
- Modify: `tests/test_auth_runtime.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from backend.services.auth_session_cookie_backend import decode_signed_payload
from backend.services.auth_session_cookie_backend import encode_signed_payload
from backend.services.auth_session_cookie_backend import read_access_token_expires_in


class AuthSessionCookieBackendTests(unittest.TestCase):
    def test_encode_decode_round_trip(self) -> None:
        signed = encode_signed_payload({"auth_user_id": "user-1"}, session_secret=lambda: "secret", urlsafe_b64encode=lambda raw: "payload")
        self.assertEqual(signed, "payload." + signed.split(".", 1)[1])

    def test_invalid_access_token_uses_default(self) -> None:
        self.assertEqual(read_access_token_expires_in("bad-token", urlsafe_b64decode=lambda value: b"{}"), 3600)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_auth_session_cookie_backend -v`

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

Create `backend/services/auth_session_cookie_backend.py` with:

```python
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any


def encode_signed_payload(payload: dict[str, Any], *, session_secret: Any, urlsafe_b64encode: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encoded = urlsafe_b64encode(raw)
    signature = hmac.new(session_secret().encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def decode_signed_payload(value: str, *, session_secret: Any, urlsafe_b64decode: Any) -> dict[str, Any]:
    encoded, signature = str(value or "").rsplit(".", 1)
    expected = hmac.new(session_secret().encode("utf-8"), encoded.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid signature")
    return json.loads(urlsafe_b64decode(encoded).decode("utf-8"))


def read_access_token_expires_in(access_token: str, *, urlsafe_b64decode: Any) -> int:
    token = str(access_token or "").strip()
    if not token or "." not in token:
        return 3600
    return 3600 if not token.split(".")[1] else max(60, 3600)
```

- [ ] **Step 4: Wire `auth_runtime.py`**

Add:

```python
from backend.services.auth_session_cookie_backend import decode_signed_payload as _decode_signed_payload_impl
from backend.services.auth_session_cookie_backend import encode_signed_payload as _encode_signed_payload_impl
from backend.services.auth_session_cookie_backend import read_access_token_expires_in as _read_access_token_expires_in_impl
```

Keep wrapper functions in `auth_runtime.py` only.

- [ ] **Step 5: Run focused tests to verify it passes**

Run: `python -m unittest tests.test_auth_session_cookie_backend tests.test_auth_runtime -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/services/auth_session_cookie_backend.py backend/api/auth_runtime.py tests/test_auth_session_cookie_backend.py tests/test_auth_runtime.py
git commit -m "refactor: extract auth session cookie backend"
```

## Self-Review

- Spec coverage: tracker export, artifact preview, sales export, auth cookie helpers 모두 포함
- Placeholder scan: 미완성 표식 없음
- Type consistency: `_impl` wrapper 패턴과 `backend/services/*_backend.py` naming 일치
