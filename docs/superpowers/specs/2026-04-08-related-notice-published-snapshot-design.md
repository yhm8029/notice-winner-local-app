# Related Notice Published Snapshot Design

**Goal**

Make `Open related notices` feel instantaneous across project filters by serving only from a published related-notice snapshot set, never from request-time search or request-time precompute.

**Scope**

- `backend/services/run_execution.py`
- related notice snapshot storage and publish metadata
- `backend/api/app.py`
- related notice read-model helpers and targeted tests

**Out of Scope**

- changing related notice scoring or query generation
- changing project list filter semantics
- redesigning the related notice UI

**Problem**

- the current request path can still return `pending` or seed fallback behavior when a project has not been precomputed yet
- button-click latency is therefore inconsistent: some projects open immediately, others wait on background precompute state
- users expect related notices to open with the same immediacy as the rest of the project board, even after changing filters such as `Seoul -> Busan`
- precomputing everything on every request is too expensive, but request-time variability is no longer acceptable

**Design Summary**

Use a published snapshot-set model:

1. build the next related-notice snapshot set during or immediately after a successful `project_tracker` collection pipeline
2. keep the current published set visible while the new set is being prepared
3. publish the new set only after it is complete and valid
4. serve `/api/projects/{project_id}/related-notices` only from the currently published set
5. remove request-time queueing as the normal user path

This gives users near-constant open latency while keeping compute cost bounded to pipeline completion events.

## Architecture

### Current Published Set

- Introduce a publish concept for related notices.
- Every related-notice cache row belongs to a snapshot set version, for example `snapshot_set_id`.
- A separate publish pointer identifies which snapshot set is live for reads.
- Project list reads and related-notice detail reads must resolve against the same live publish pointer.

### Next Snapshot Set

- When a new `project_tracker` run succeeds, the backend computes a full candidate related-notice snapshot set for that run.
- Candidate rows are written under a new snapshot-set identifier without disturbing the currently published set.
- The candidate set is not user-visible until it passes completion checks.

### Publish Step

- Once the candidate set is complete, atomically switch the publish pointer from the old set to the new set.
- After the switch, all related-notice reads use the new set immediately.
- The old set can remain available temporarily for rollback or cleanup.

## Components

### Snapshot Storage

- Reuse `project_related_notice_cache` as the per-project snapshot row store.
- Extend rows with snapshot-set identity so old and new sets can coexist safely.
- Add a lightweight publish manifest or pointer store that records:
  - current live snapshot-set id
  - source run id
  - generated/published timestamps
  - readiness status

### Pipeline Integration

- Related-notice snapshot generation becomes part of the successful run completion flow.
- The pipeline may compute related notices incrementally internally, but user-visible publication happens only after the final set is complete.
- The effective contract becomes: a new run does not replace user-visible related notices until its snapshot set is ready to publish.

### Read Path

- `/api/projects/{project_id}/related-notices` first resolves the current published snapshot-set id.
- It then reads the matching project row only from that set.
- If the project is absent from the published set, return a stable empty/missing response instead of triggering heavy background work.
- Request-time queueing or precompute kick-off is removed from the default user path.

## Data Flow

### Successful Run

1. `project_tracker` finishes core collection/filter/rescan/export work.
2. related-notice snapshot generation builds a candidate set for all relevant projects in that run scope.
3. candidate rows are written with the new snapshot-set id.
4. completion validation verifies the set is internally consistent.
5. publish pointer flips to the new snapshot set.
6. subsequent reads for any filter combination return from the new published set immediately.

### While a New Run Is In Progress

- The UI continues to read from the previous published set.
- Filter changes such as `Seoul -> Busan` only change which project records are displayed; they do not trigger related-notice recomputation.
- Related notices therefore remain immediately openable for projects covered by the currently published set.

## Failure Handling

- If candidate snapshot generation fails for any required project, the new set is not published.
- The previous published set remains live.
- Users keep instant responses, but related notices stay one publish cycle behind until a later successful run.
- Operational logs must record the failed generation and the fact that publish was withheld.

### New Projects Missing From Published Set

- If a project first appears in a failed candidate set, it will not gain immediate related notices until a later successful publish.
- The user path should show a stable empty or unavailable state for that project instead of degrading into slow live search.

## UX Contract

- `Open related notices` should be effectively immediate for published projects.
- Switching filters must not introduce fresh loading waits for related notices.
- Users may briefly see slightly stale related notices during an active pipeline run, but they should not see request-time recomputation states as the normal case.

## Testing

- verify project related-notice reads use only the published snapshot set
- verify filter changes still produce immediate related-notice opens for projects in the live set
- verify a new successful run does not become visible until publish pointer switch
- verify candidate generation failure leaves the previous published set active
- verify the default read path no longer queues request-time precompute work

## Risks And Tradeoffs

- freshness becomes publish-cycle based rather than request-time recoverable
- snapshot-set metadata adds implementation complexity compared with the current per-project cache rows
- rollback and cleanup rules need to be explicit so stale sets do not accumulate indefinitely

**Recommendation**

Adopt the explicit snapshot-set plus publish-pointer model rather than a lighter row-version flag only. The pointer model is easier to reason about, supports atomic cutover, and better matches the requirement that filter changes should still feel globally instant.

**Success Criteria**

- `Open related notices` opens from published data with near-constant latency
- changing project filters does not reintroduce per-project wait states
- request-time background precompute is no longer part of the standard user path
- related-notice reads stay consistent within a single published snapshot set
- failed snapshot generation does not partially leak into user-visible reads
