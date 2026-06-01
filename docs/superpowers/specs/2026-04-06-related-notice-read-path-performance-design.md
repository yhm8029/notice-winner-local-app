# Related Notice Read Path Performance Design

**Goal**

Reduce `/api/projects/{project_id}/related-notices` latency by ensuring the request path only returns cached or lightweight fallback data and never performs heavy precomputed artifact scans inline.

**Scope**

- `backend/api/app.py`
- `backend/services/related_notice_read_model_backend.py`
- targeted tests for related notice read-path behavior

**Out of Scope**

- changing related notice matching logic
- changing background precompute payload format
- frontend UI redesign

**Current Problem**

- production logs show `/api/projects/.../related-notices` taking `68s` to `159s`
- the route does not call live notice search directly, but it still attempts expensive precomputed lookup work on cache miss
- `precomputed_related_notice_items()` falls back from Supabase cache to per-run artifact scans, reading `related_notices_json` payloads during the user request
- while those requests are in flight, the server also queues background precompute work, causing additional churn

**Design**

Use a strict fast read path:

1. request-scoped cache hit: return immediately
2. Supabase `project_related_notice_cache` hit: return immediately
3. otherwise skip artifact scan on the request path
4. fall back to `related_notice_response_without_live()` for seed/pending behavior
5. keep background precompute queue behavior so freshness can recover asynchronously

**Why**

- users tolerate slightly stale related notices better than minute-long blocking requests
- background precompute already exists and is the right place for heavyweight rebuild work
- the most direct latency win is removing artifact traversal from request handling

**Success Criteria**

- `/api/projects/.../related-notices` no longer scans `related_notices_json` artifacts on cache miss
- request path still returns `precomputed`, `seed_fallback`, `pending`, or `failed` responses with existing contracts
- background precompute still queues as before
- targeted tests stay green

**Operational Note 2026-04-09**

- shared production DB canary verification used a one-time additive bootstrap in Supabase SQL Editor
- that bootstrap added `project_related_notice_cache.snapshot_set_id`, created `related_notice_publications`, and published existing cache rows as `legacy`
- it intentionally did not replace the current `(organization_id, project_key)` uniqueness contract, so current main writes remained compatible during canary testing
- the temporary SQL helper used for that bootstrap is not part of the product runtime contract and is intentionally excluded from this PR

**Scale-Up Note 2026-04-09**

- current optimization direction is `cache reuse first`: reuse published or `legacy` related-notice cache entries during full snapshot rebuilds and only live-recompute cache misses or stale entries
- if project volume or rebuild time grows enough that cache-first full publish is still too slow, the next architecture step is `project-level incremental recompute queue`
- that queue-based design should keep the published snapshot contract, but distribute recompute work per project instead of blocking the entire publish on one large full rebuild
