# Tracker Opening Date Default Sort Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the default tracker notice list ordering to `opening_scheduled_date` descending with blank dates pushed to the bottom, while keeping deterministic fallback ordering.

**Architecture:** Centralize the default tracker ordering rule in the backend tracker global-summary path, then reuse that ordered output for the home bootstrap first-page payload. Keep the change localized to tracker ordering helpers and update tests to prove dated rows sort first, blank rows sort last, and bootstrap metadata reflects the new default contract.

**Tech Stack:** Python, FastAPI, unittest

---

### Task 1: Add failing tests for the new default tracker ordering

**Files:**
- Modify: `tests/test_tracker_global_summary.py`
- Modify: `tests/test_home_bootstrap_payload.py`

- [ ] **Step 1: Write the failing global ordering test**

```python
    def test_filter_tracker_rows_for_global_scope_orders_by_opening_scheduled_date_desc_with_blanks_last(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "blank",
                    "project_name": "Blank Date Project",
                    "opening_scheduled_date": "",
                    "updated_at": "2026-04-14T03:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "older-dated",
                    "project_name": "Older Date Project",
                    "opening_scheduled_date": "2026-03-02",
                    "updated_at": "2026-04-14T02:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "newer-dated",
                    "project_name": "Newer Date Project",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T01:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual(
            [row["id"] for row in filtered],
            ["newer-dated", "older-dated", "blank"],
        )
```

- [ ] **Step 2: Write the failing tie-break test for deterministic fallback ordering**

```python
    def test_filter_tracker_rows_for_global_scope_keeps_updated_at_fallback_for_same_opening_date(self) -> None:
        filtered = _filter_tracker_rows_for_global_scope(
            [
                {
                    "id": "older-update",
                    "project_name": "Alpha",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T01:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
                {
                    "id": "newer-update",
                    "project_name": "Beta",
                    "opening_scheduled_date": "2026-04-01",
                    "updated_at": "2026-04-14T02:00:00+00:00",
                    "has_overrides": False,
                    "overridden_fields": [],
                },
            ],
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
        )

        self.assertEqual(
            [row["id"] for row in filtered],
            ["newer-update", "older-update"],
        )
```

- [ ] **Step 3: Write the failing bootstrap metadata test**

```python
    def test_describe_home_bootstrap_snapshot_state_accepts_opening_date_sort_contract(self) -> None:
        snapshot = {
            "snapshot_version": 3,
            "generated_at": "2026-03-29T00:00:00+00:00",
            "payload_json": {
                "snapshot_version": 3,
                "generated_at": "2026-03-29T00:00:00+00:00",
                "my_items": [],
                "company_items": [],
                "organization_users": [],
                "tracker_first_page": {
                    "items": [{"id": "1", "project_name": "Alpha"}],
                    "page": 1,
                    "page_size": 20,
                    "total": 1,
                    "sort_contract": {
                        "mode": "default",
                        "order_by": [
                            "opening_scheduled_date_desc",
                            "updated_at_desc",
                            "id_desc",
                        ],
                    },
                },
            },
        }

        self.assertEqual(_describe_home_bootstrap_snapshot_state(snapshot), "ready")
```

- [ ] **Step 4: Run `python -m unittest tests.test_tracker_global_summary tests.test_home_bootstrap_payload -v` and confirm the new assertions fail for the missing ordering behavior/metadata**

### Task 2: Implement the backend default ordering rule

**Files:**
- Modify: `backend/services/tracker_global_summary_backend.py`

- [ ] **Step 1: Add a dedicated sort-key helper for tracker default ordering**

```python
def _tracker_default_sort_key(row: dict[str, Any]) -> tuple[int, str, str, str]:
    opening_scheduled_date = str(row.get("opening_scheduled_date") or "").strip()
    has_blank_opening_date = 1 if not opening_scheduled_date else 0
    updated_at = str(row.get("updated_at") or "")
    row_id = str(row.get("id") or "")
    return (
        has_blank_opening_date,
        opening_scheduled_date,
        updated_at,
        row_id,
    )
```

- [ ] **Step 2: Apply the helper at the end of global-scope filtering**

```python
def filter_tracker_rows_for_global_scope(... ) -> list[dict[str, Any]]:
    q_norm = norm_text_fn(q)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        ...
        filtered.append(dict(row))
    filtered.sort(key=_tracker_default_sort_key, reverse=True)
    return filtered
```

- [ ] **Step 3: Keep collapsed project rows deterministic without changing collapse semantics**

```python
def collapse_tracker_rows_by_project(... ) -> list[dict[str, Any]]:
    ...
    for row in collapsed:
        row["_search_text_norm"] = norm_text_fn(_build_tracker_row_search_bucket(row))
    collapsed.sort(key=lambda row: (str(row.get("updated_at") or ""), str(row.get("id") or "")), reverse=True)
    return collapsed
```

- [ ] **Step 4: Run `python -m unittest tests.test_tracker_global_summary tests.test_home_bootstrap_payload -v` and confirm the ordering tests still fail only on bootstrap metadata**

### Task 3: Update bootstrap sort metadata and re-verify targeted regressions

**Files:**
- Modify: `backend/services/home_bootstrap_backend.py`
- Modify: `tests/test_home_bootstrap_payload.py`
- Verify: `tests/test_tracker_global_summary.py`

- [ ] **Step 1: Update the bootstrap sort contract to advertise the new default order**

```python
    return {
        "items": [model_to_json_dict(to_tracker_entry_summary_model(item)) for item in items],
        "page": 1,
        "page_size": page_size,
        "total": total,
        "sort_contract": {
            "mode": "default",
            "order_by": [
                "opening_scheduled_date_desc",
                "updated_at_desc",
                "id_desc",
            ],
        },
    }
```

- [ ] **Step 2: Re-run `python -m unittest tests.test_tracker_global_summary tests.test_home_bootstrap_payload -v` and confirm green**

- [ ] **Step 3: Run targeted tracker regressions**

```bash
python -m unittest tests.test_tracker_entry_opening_dates -v
python -m unittest tests.test_tracker_global_summary -v
```

Expected: both command groups pass with no new failures.

- [ ] **Step 4: Run `git diff --stat` and review that the patch is limited to tracker ordering logic, bootstrap sort metadata, and tests**
