# App Router Modularization Design

**Goal**

Split the oversized FastAPI application module into domain routers without changing user-visible behavior, response contracts, or deployment topology.

**Current State**

- `backend/api/app.py` is about 5000 lines long and currently defines roughly 74 routes.
- The file mixes route registration, request handlers, helper functions, startup wiring, and cross-domain logic.
- Recent work reduced startup memory pressure by lazy-loading rare heavy paths, but ongoing optimization is harder because import boundaries are still centered on one large module.
- The current structure also increases regression risk because unrelated features share one file and one import graph.

**Problem**

The backend entry module is doing too much:

- route definitions for multiple domains live together
- feature-specific helpers are interleaved with unrelated endpoints
- memory and import optimization requires editing one large file repeatedly
- testing and review are harder because small changes create broad diffs

This is now a maintainability problem first, and a performance-enabler problem second.

**Scope**

Phase 1 modularization will only move route definitions into domain router modules.

In scope:

- split route declarations by domain
- preserve existing helpers and behavior as much as possible
- keep one FastAPI app and one deployment target
- keep current auth/session optimizations and startup lazy-loading changes

Out of scope:

- changing API response shapes
- changing URL paths
- splitting into multiple deployable services
- broad service-layer refactors
- repository-layer redesign

**Recommended Approach**

Move routes into domain router modules first, while keeping the current helper implementations available from existing modules.

Recommended router split:

- `backend/api/routers/auth.py`
- `backend/api/routers/admin.py`
- `backend/api/routers/tracker.py`
- `backend/api/routers/artifacts.py`
- `backend/api/routers/related_notice.py`
- optional small router for health/static shell routes if needed

`backend/api/app.py` should become a thinner composition root that:

- creates the FastAPI app
- mounts static files
- registers middleware
- includes routers
- keeps only truly app-level wiring

Why this approach:

- lowest regression risk
- easiest to review
- makes future memory work more local and less invasive
- preserves current deployment behavior

**Rejected Approach**

Move routes and helpers and service logic all at once.

This would create a cleaner architecture in one pass, but it is too risky for the next step. The current priority is safe structural separation, not sweeping redesign.

**Target Structure**

Phase 1 target:

- `backend/api/app.py`
  - FastAPI app creation
  - middleware registration
  - router inclusion
  - static/app shell routes only if those are truly global
- `backend/api/routers/auth.py`
  - sign-in, sign-up, session, profile, invitation/auth-adjacent endpoints
- `backend/api/routers/admin.py`
  - admin-only account and audit endpoints
- `backend/api/routers/tracker.py`
  - tracker entry listing/detail/update/export/missing report flows
- `backend/api/routers/artifacts.py`
  - artifact listing/download/preview
- `backend/api/routers/related_notice.py`
  - related notice read/search/view endpoints

**Dependency Rules**

Phase 1 rules:

- router modules may import existing helper functions from `backend.api.app` only if needed to reduce immediate churn
- but new heavy imports should not be added back to app startup
- startup-sensitive helpers should remain lazy-loaded where already optimized
- domain routers should prefer concrete imports over package-root fan-out imports

This means the first split may not be architecturally perfect, but it keeps risk controlled.

**Migration Strategy**

Implement in small slices.

Recommended order:

1. Extract `auth` router
2. Extract `admin` router
3. Extract `artifacts` router
4. Extract `related_notice` router
5. Extract `tracker` router last because it is the largest and most entangled
6. Reduce `app.py` to composition root

Why this order:

- `auth` and `admin` are easier to verify and form a stable baseline
- `tracker` has the most helper coupling and should be moved after router patterns are proven

**Behavior Preservation**

The following must remain unchanged:

- request/response models
- route paths and methods
- middleware behavior
- auth/session cookie behavior
- background task triggering
- static shell behavior for `/` and `/app`

The only intended user-visible effect is lower maintenance risk; runtime behavior should remain the same.

**Testing Strategy**

Required checks after each extraction step:

- auth runtime tests
- admin account API tests
- startup import tests
- frontend auth session tests
- syntax check for touched frontend/backend entry files

After the full router split:

- rerun targeted backend tests for touched domains
- verify router registration in the composed app
- compare import-time again to confirm modularization did not regress startup

**Success Criteria**

- `backend/api/app.py` is substantially smaller and acts mainly as composition root
- domain routes live in focused router modules
- existing tests remain green
- current startup memory optimizations remain intact
- future memory or behavior work can be made within one router domain without editing a 5000-line file

**Follow-up After Phase 1**

If router extraction is stable, Phase 2 can clean helper boundaries:

- move domain-specific helpers out of `app.py`
- reduce cross-router helper imports
- shrink common import graph further
- revisit repository/schema imports that still appear on hot startup paths
