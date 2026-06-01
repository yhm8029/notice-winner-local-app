# Related Notice Published Snapshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make project related notices open from a published snapshot set with stable low latency, even after project filter changes.

**Architecture:** Extend the existing per-project related notice cache with `snapshot_set_id`, add a separate publication pointer repository, build candidate snapshot sets during successful run finalization, and switch the read path to only serve rows from the currently published set. Keep the previous published set live until the next candidate set is complete so users never see partial updates.

**Tech Stack:** Python, FastAPI, Supabase/PostgREST, in-memory repositories, pytest/unittest

---

## File Map

- `supabase/migrations/202604080001_related_notice_publications.sql`
  Adds `snapshot_set_id` support to `project_related_notice_cache` and creates the `related_notice_publications` table.
- `supabase/manual_bootstrap.sql`
  Mirrors the new migration for local/manual bootstrap environments.
- `backend/repositories/related_notice_cache.py`
  Expands the cache repository contract to support snapshot-set aware reads.
- `backend/repositories/in_memory_related_notice_cache.py`
  Stores multiple cache rows per `project_key` across snapshot sets.
- `backend/repositories/supabase_related_notice_cache.py`
  Adds `snapshot_set_id` to selects, upserts, and filtered reads.
- `backend/repositories/related_notice_publications.py`
  Defines the publication pointer repository protocol and row shape.
- `backend/repositories/in_memory_related_notice_publications.py`
  In-memory publication pointer storage for tests.
- `backend/repositories/supabase_related_notice_publications.py`
  Supabase implementation for the publication pointer table.
- `backend/repositories/factory.py`
  Registers the new publication repository and reset helper.
- `backend/repositories/__init__.py`
  Re-exports the new publication repository interfaces.
- `backend/services/related_notice_publish_backend.py`
  New service module that writes candidate snapshot sets and atomically flips the publication pointer.
- `backend/services/run_execution.py`
  Calls the publish backend after successful related-notice payload generation.
- `backend/services/related_notice_read_model_backend.py`
  Reads only the currently published snapshot-set rows on the request path.
- `backend/api/app.py`
  Stops request-time queueing for `/api/projects/{project_id}/related-notices` and returns stable published/missing responses.
- `tests/test_related_notice_publish_backend.py`
  Covers candidate generation, publish cutover, and failed publish retention.
- `tests/test_related_notice_read_model_backend.py`
  Covers published-set-only reads and snapshot-set isolation.
- `tests/test_related_notice_helpers.py`
  Covers the request route behavior after queue removal.
- `tests/test_repository_factory.py`
  Covers factory wiring for the new publication repository.
- `tests/api/test_phase1_api.py`
  Covers end-to-end publish behavior after a successful run.

### Task 1: Add Snapshot-Set Storage And Publication Repository

**Files:**
- Create: `supabase/migrations/202604080001_related_notice_publications.sql`
- Modify: `supabase/manual_bootstrap.sql`
- Modify: `backend/repositories/related_notice_cache.py`
- Modify: `backend/repositories/in_memory_related_notice_cache.py`
- Modify: `backend/repositories/supabase_related_notice_cache.py`
- Create: `backend/repositories/related_notice_publications.py`
- Create: `backend/repositories/in_memory_related_notice_publications.py`
- Create: `backend/repositories/supabase_related_notice_publications.py`
- Modify: `backend/repositories/factory.py`
- Modify: `backend/repositories/__init__.py`
- Test: `tests/test_repository_factory.py`

- [ ] **Step 1: Write the failing repository tests**

```python
def test_in_memory_related_notice_cache_keeps_rows_per_snapshot_set() -> None:
    repository = InMemoryRelatedNoticeCacheRepository()
    repository.upsert_cache({"project_key": "school", "snapshot_set_id": "set-a", "status": "success", "payload_json": {"items": [{"id": "a"}]}})
    repository.upsert_cache({"project_key": "school", "snapshot_set_id": "set-b", "status": "success", "payload_json": {"items": [{"id": "b"}]}})

    assert repository.get_cache(project_key="school", snapshot_set_id="set-a")["payload_json"]["items"][0]["id"] == "a"
    assert repository.get_cache(project_key="school", snapshot_set_id="set-b")["payload_json"]["items"][0]["id"] == "b"


def test_repository_factory_reports_related_notice_publications_backend() -> None:
    summary = describe_repository_backends()
    assert "related_notice_publications" in summary
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_repository_factory.py -k "related_notice_publications or snapshot_set" -v`

Expected: FAIL with errors such as `TypeError: get_cache() got an unexpected keyword argument 'snapshot_set_id'` and missing factory summary key assertions.

- [ ] **Step 3: Write the minimal storage implementation**

```python
class RelatedNoticeCacheRepository(Protocol):
    def get_cache(self, *, project_key: str, snapshot_set_id: str | None = None) -> RelatedNoticeCacheRow | None:
        pass

    def upsert_cache(self, row: RelatedNoticeCacheRow) -> RelatedNoticeCacheRow:
        pass


class RelatedNoticePublicationRepository(Protocol):
    def get_publication(self, *, organization_id: UUID) -> RelatedNoticePublicationRow | None:
        pass

    def upsert_publication(
        self,
        *,
        organization_id: UUID,
        published_snapshot_set_id: str,
        source_run_id: UUID,
        generated_at: Any,
        published_at: Any,
    ) -> RelatedNoticePublicationRow | None:
        pass
```

```sql
alter table public.project_related_notice_cache
  add column if not exists snapshot_set_id text not null default 'legacy';

drop index if exists idx_project_related_notice_cache_org_key;
create unique index idx_project_related_notice_cache_org_snapshot_project
  on public.project_related_notice_cache (organization_id, snapshot_set_id, project_key);

create table public.related_notice_publications (
  organization_id uuid primary key,
  published_snapshot_set_id text not null,
  source_run_id uuid not null,
  generated_at timestamptz not null,
  published_at timestamptz not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_repository_factory.py -k "related_notice_publications or snapshot_set" -v`

Expected: PASS with the new repository summary key present and snapshot-set reads isolated by `snapshot_set_id`.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/202604080001_related_notice_publications.sql supabase/manual_bootstrap.sql backend/repositories/related_notice_cache.py backend/repositories/in_memory_related_notice_cache.py backend/repositories/supabase_related_notice_cache.py backend/repositories/related_notice_publications.py backend/repositories/in_memory_related_notice_publications.py backend/repositories/supabase_related_notice_publications.py backend/repositories/factory.py backend/repositories/__init__.py tests/test_repository_factory.py
git commit -m "feat: add related notice publication storage"
```

### Task 2: Build Candidate Snapshot Writing And Publish Cutover

**Files:**
- Create: `backend/services/related_notice_publish_backend.py`
- Modify: `backend/services/run_execution.py`
- Test: `tests/test_related_notice_publish_backend.py`

- [ ] **Step 1: Write the failing publish-backend tests**

```python
def test_publish_related_notice_snapshot_set_flips_pointer_after_candidate_write() -> None:
    cache_repository = InMemoryRelatedNoticeCacheRepository()
    publication_repository = InMemoryRelatedNoticePublicationRepository()
    payload = {
        "run_id": "run-1",
        "generated_at": "2026-04-08T00:00:00+00:00",
        "projects": [{"project_key": "school", "project_name": "School", "project_search_name": "school", "issuer_name": "Seoul", "items": [{"id": "notice-1"}], "item_count": 1, "algorithm_version": 11, "source": "live"}],
    }

    snapshot_set_id = publish_related_notice_snapshot_set(
        run_id=UUID("11111111-1111-1111-1111-111111111111"),
        payload=payload,
        cache_repository=cache_repository,
        publication_repository=publication_repository,
    )

    publication = publication_repository.get_publication(organization_id=DEFAULT_PHASE1_ORGANIZATION_ID)
    assert publication["published_snapshot_set_id"] == snapshot_set_id
    assert cache_repository.get_cache(project_key="school", snapshot_set_id=snapshot_set_id) is not None


def test_publish_related_notice_snapshot_set_keeps_previous_pointer_on_failure() -> None:
    publication_repository = InMemoryRelatedNoticePublicationRepository(
        initial_row={
            "organization_id": DEFAULT_PHASE1_ORGANIZATION_ID,
            "published_snapshot_set_id": "set-live",
            "source_run_id": "11111111-1111-1111-1111-111111111111",
            "generated_at": "2026-04-08T00:00:00+00:00",
            "published_at": "2026-04-08T00:00:00+00:00",
        }
    )

    class ExplodingCacheRepository:
        def upsert_cache(self, row):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        publish_related_notice_snapshot_set(
            run_id=UUID("22222222-2222-2222-2222-222222222222"),
            payload={
                "run_id": "run-2",
                "generated_at": "2026-04-08T00:05:00+00:00",
                "projects": [{"project_key": "broken", "project_name": "Broken", "project_search_name": "broken", "issuer_name": "Busan", "items": [{"id": "notice-2"}], "item_count": 1, "algorithm_version": 11, "source": "live"}],
            },
            cache_repository=ExplodingCacheRepository(),
            publication_repository=publication_repository,
        )

    assert publication_repository.get_publication(organization_id=DEFAULT_PHASE1_ORGANIZATION_ID)["published_snapshot_set_id"] == "set-live"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_related_notice_publish_backend.py -v`

Expected: FAIL because `publish_related_notice_snapshot_set` and the in-memory publication repository do not exist yet.

- [ ] **Step 3: Write the minimal publish backend**

```python
def publish_related_notice_snapshot_set(*, run_id: UUID, payload: dict[str, Any], cache_repository: Any, publication_repository: Any, utc_now: Any = _utcnow) -> str:
    snapshot_set_id = uuid4().hex
    generated_at = payload.get("generated_at") or utc_now().isoformat()
    for project_entry in list(payload.get("projects") or []):
        cache_repository.upsert_cache(
            {
                "project_key": str(project_entry.get("project_key") or "").strip(),
                "snapshot_set_id": snapshot_set_id,
                "project_name": str(project_entry.get("project_name") or ""),
                "project_search_name": str(project_entry.get("project_search_name") or ""),
                "issuer_name": str(project_entry.get("issuer_name") or ""),
                "status": "success",
                "source": str(project_entry.get("source") or "published_snapshot"),
                "algorithm_version": int(project_entry.get("algorithm_version") or 0),
                "item_count": len(list(project_entry.get("items") or [])),
                "error": "",
                "payload_json": dict(project_entry),
                "source_run_id": str(run_id),
                "generated_at": generated_at,
            }
        )
    publication_repository.upsert_publication(
        organization_id=load_phase1_identity().organization_id,
        published_snapshot_set_id=snapshot_set_id,
        source_run_id=run_id,
        generated_at=generated_at,
        published_at=utc_now().isoformat(),
    )
    return snapshot_set_id
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_related_notice_publish_backend.py -v`

Expected: PASS with one test proving atomic pointer cutover and one proving failed candidate writes preserve the previous published pointer.

- [ ] **Step 5: Commit**

```bash
git add backend/services/related_notice_publish_backend.py backend/services/run_execution.py tests/test_related_notice_publish_backend.py
git commit -m "feat: publish related notice snapshot sets"
```

### Task 3: Wire Successful Runs To Publish Snapshot Sets

**Files:**
- Modify: `backend/services/run_execution.py`
- Test: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Write the failing run-execution/API test**

```python
def test_project_tracker_run_publishes_related_notice_snapshot_set(self) -> None:
    from backend.phase1_defaults import load_phase1_identity
    from backend.repositories import get_related_notice_publication_repository

    with ApiServer() as server:
        create_status, create_payload = server.request_json("POST", "/api/runs", payload=_project_tracker_run_payload())
        self.assertEqual(create_status, 202)
        run_detail, _artifacts = _wait_for_related_notice_precompute(server, create_payload["id"])

        publication = get_related_notice_publication_repository().get_publication(
            organization_id=load_phase1_identity().organization_id
        )
        self.assertIsNotNone(publication)
        self.assertEqual(str(publication["source_run_id"]), create_payload["id"])
        self.assertTrue(publication["published_snapshot_set_id"])
        self.assertEqual(run_detail["summary"]["output"]["related_notice_precompute_status"], "success")
```

- [ ] **Step 2: Run the API test to verify it fails**

Run: `.\.venv\Scripts\python.exe -m pytest tests/api/test_phase1_api.py -k publishes_related_notice_snapshot_set -v`

Expected: FAIL because no publication pointer exists and the run finalization path still only writes cache rows/artifacts.

- [ ] **Step 3: Implement the run finalization hook**

```python
related_notice_payload = _build_related_notice_artifact_payload(
    run_id=run_id,
    params=params,
    seed_rows=seed_rows,
    target_project_keys=None,
    limit_projects=False,
)
published_snapshot_set_id = publish_related_notice_snapshot_set(
    run_id=run_id,
    payload=related_notice_payload,
    cache_repository=get_related_notice_cache_repository(),
    publication_repository=get_related_notice_publication_repository(),
)
_update_related_notice_summary(
    run_id=run_id,
    summary_patch={
        "related_notice_precomputed": True,
        "related_notice_precompute_status": "success",
        "related_notice_snapshot_set_id": published_snapshot_set_id,
    },
)
```

- [ ] **Step 4: Run the API test to verify it passes**

Run: `.\.venv\Scripts\python.exe -m pytest tests/api/test_phase1_api.py -k publishes_related_notice_snapshot_set -v`

Expected: PASS with the run summary carrying `related_notice_snapshot_set_id` and the publication pointer referencing the same successful run.

- [ ] **Step 5: Commit**

```bash
git add backend/services/run_execution.py tests/api/test_phase1_api.py
git commit -m "feat: publish related notices after successful runs"
```

### Task 4: Switch The Read Path To Published Snapshot Reads Only

**Files:**
- Modify: `backend/services/related_notice_read_model_backend.py`
- Modify: `backend/api/app.py`
- Test: `tests/test_related_notice_read_model_backend.py`
- Test: `tests/test_related_notice_helpers.py`

- [ ] **Step 1: Write the failing read-path tests**

```python
def test_precomputed_related_notice_items_reads_only_published_snapshot_set() -> None:
    class FakePublicationRepository:
        def get_publication(self, *, organization_id):  # type: ignore[no-untyped-def]
            return {"published_snapshot_set_id": "set-live"}

    class FakeCacheRepository:
        def __init__(self, rows):  # type: ignore[no-untyped-def]
            self._rows = rows

        def get_cache(self, *, project_key, snapshot_set_id=None):  # type: ignore[no-untyped-def]
            return self._rows.get((project_key, snapshot_set_id))

        def upsert_cache(self, row):  # type: ignore[no-untyped-def]
            return row

    publication_repo = FakePublicationRepository()
    cache_repo = FakeCacheRepository(
        {
            ("school", "set-live"): {"project_key": "school", "snapshot_set_id": "set-live", "algorithm_version": 11, "payload_json": {"items": [{"id": "live"}]}},
            ("school", "set-next"): {"project_key": "school", "snapshot_set_id": "set-next", "algorithm_version": 11, "payload_json": {"items": [{"id": "next"}]}},
        }
    )

    items, has_precomputed = precomputed_related_notice_items(
        {"_project_match_key": "school"},
        get_related_notice_cache_repository_fn=lambda: cache_repo,
        get_related_notice_publication_repository_fn=lambda: publication_repo,
        allow_artifact_scan=False,
    )

    assert has_precomputed is True
    assert [item.id for item in items] == ["live"]


def test_list_related_notices_for_project_does_not_queue_request_time_precompute() -> None:
    project_id = uuid4()
    project = {"project_name": "Demo", "project_search_name": "Demo", "_project_match_key": "demo", "issuer_name": "Seoul"}

    with patch("backend.api.app._get_project_aggregate", return_value=project), patch(
        "backend.api.app._precomputed_related_notice_items", return_value=([], False)
    ), patch("backend.api.app.queue_related_notice_precompute_for_run", side_effect=AssertionError("should not queue")):
        response = _list_related_notices_for_project(project_id)

    assert response.status == "missing"
    assert response.source == "published_snapshot"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_related_notice_read_model_backend.py tests/test_related_notice_helpers.py -k "published_snapshot_set or does_not_queue_request_time_precompute" -v`

Expected: FAIL because the read model does not know about publication pointers and the route still falls through to `_related_notice_response_without_live`.

- [ ] **Step 3: Write the minimal read-path implementation**

```python
publication = get_related_notice_publication_repository_fn().get_publication(
    organization_id=load_phase1_identity().organization_id,
)
snapshot_set_id = str((publication or {}).get("published_snapshot_set_id") or "").strip()
if not snapshot_set_id:
    return [], False

cache_row = cache_repository.get_cache(project_key=target_key, snapshot_set_id=snapshot_set_id)
```

```python
items, has_precomputed = _precomputed_related_notice_items(
    project,
    trace_id=trace_id,
    project_id=project_id,
    allow_artifact_scan=False,
)
if not has_precomputed:
    response = RelatedNoticeListResponse(
        project_id=project_id,
        project_name=str(project.get("project_name") or ""),
        project_search_name=str(project.get("project_search_name") or ""),
        status="missing",
        source="published_snapshot",
        message="related notices are not available in the current published snapshot",
        precomputed=False,
        items=[],
    )
    return _set_related_notice_response_cache(project_id, response)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_related_notice_read_model_backend.py tests/test_related_notice_helpers.py -k "published_snapshot_set or does_not_queue_request_time_precompute" -v`

Expected: PASS with the live snapshot-set row selected and no request-time queueing performed on a miss.

- [ ] **Step 5: Commit**

```bash
git add backend/services/related_notice_read_model_backend.py backend/api/app.py tests/test_related_notice_read_model_backend.py tests/test_related_notice_helpers.py
git commit -m "feat: serve related notices from published snapshots"
```

### Task 5: Run Focused Regression Verification

**Files:**
- Verify: `tests/test_repository_factory.py`
- Verify: `tests/test_related_notice_publish_backend.py`
- Verify: `tests/test_related_notice_read_model_backend.py`
- Verify: `tests/test_related_notice_helpers.py`
- Verify: `tests/api/test_phase1_api.py`

- [ ] **Step 1: Run the focused regression suite**

Run: `.\.venv\Scripts\python.exe -m pytest tests/test_repository_factory.py tests/test_related_notice_publish_backend.py tests/test_related_notice_read_model_backend.py tests/test_related_notice_helpers.py tests/api/test_phase1_api.py -v`

Expected: PASS with no request-time related-notice queue assertions firing and the new publication pointer tests green.

- [ ] **Step 2: Inspect the working tree**

Run: `git status --short`

Expected: only the snapshot publish implementation files and tests from Tasks 1-4 remain modified.

- [ ] **Step 3: Record the final integration commit**

```bash
git add backend/api/app.py backend/repositories backend/services/run_execution.py backend/services/related_notice_publish_backend.py backend/services/related_notice_read_model_backend.py supabase/migrations/202604080001_related_notice_publications.sql supabase/manual_bootstrap.sql tests
git commit -m "feat: publish related notice snapshots for fast reads"
```

## Self-Review

- Spec coverage: Task 1 adds snapshot-set storage and the publish pointer. Task 2 builds candidate-set publication. Task 3 wires successful runs to publish the new set after completion. Task 4 moves reads to the currently published set and removes request-time queueing from the default route. Task 5 verifies the focused regression surface.
- Placeholder scan: no deferred implementation markers remain.
- Type consistency: the plan uses `snapshot_set_id` for cache rows and `published_snapshot_set_id` for the publication pointer throughout.
