# Backend Memory Footprint Reduction Design

**Goal**

Reduce backend idle memory usage into the 700-900MB range and eliminate swap thrashing during normal login, home bootstrap, and tracker browsing flows without changing user-visible behavior.

**Scope**

- `backend/api/app.py` import and startup structure
- `backend/services/__init__.py` eager import chain
- Lazy-loading for rarely used heavy paths
- Auth/session behavior already implemented on this branch remains in place
- Targeted backend verification for unchanged common paths

**Out of Scope**

- Production deployment
- EC2 instance resizing
- Splitting the application into multiple deployable services
- Supabase schema or index changes
- Changing user-facing API contracts

**Current Problem**

- The running production process currently holds about 1.4GB RSS on a 2GB instance.
- Live inspection showed active swap usage above 1GB, sustained swap-in/swap-out activity, and high iowait.
- `backend/api/app.py` imports a very large set of modules at startup, including heavy export, document parsing, report, and related-notice paths that are not needed for login or normal console navigation.
- `backend/services/__init__.py` eagerly imports pipeline and export helpers, which pulls in document extraction code that imports `pypdf` and `fitz` during process startup.
- This means the process pays startup memory cost for rare features even when the user is only logging in or browsing the default console.

**Measured Evidence**

- Import-time profiling of `import backend.api.app` shows `backend.api.app` total import time around 2.06s.
- The heaviest shared startup chain is `backend.services`, which imports pipeline/export helpers and document extraction.
- Within that chain, `backend.services.attachment_text_extract` pulls in `pypdf` and `fitz`, and those imports are among the biggest startup costs.
- `openpyxl.Workbook` is also imported at module import time from `backend/api/app.py` even though workbook generation is not part of the hot auth path.

**Design**

Use a conservative lazy-loading pass for rare, heavy functionality while leaving hot user flows unchanged.

1. Keep hot paths eager:
   - login
   - `/api/auth/session`
   - home bootstrap
   - standard tracker list/detail browsing
   - common admin console flows

2. Make rare heavy paths lazy:
   - workbook/export helpers
   - report job helpers
   - related notice collection/search helpers
   - artifact preview/read helpers that pull document parsing stacks
   - pipeline execution helpers from `backend.services`

3. Remove shared eager import fan-out:
   - stop importing heavy pipeline/export helpers through `backend.services.__init__` during app startup
   - import those helpers from their concrete modules at the point of use

4. Preserve behavior:
   - no route removals
   - no payload shape changes
   - first request to a rare feature may pay import cost once
   - common paths should remain equal or faster due to lower memory pressure

**Approach**

**Recommended approach: targeted lazy imports in `app.py` and service entrypoints**

- Replace top-level imports of rare heavy helpers with function-local imports.
- Reduce or bypass `backend.services.__init__` so hot startup paths do not pull pipeline/export/document extraction modules.
- Keep auth/session and console startup code unchanged except for benefiting from a lighter process.

Why this approach:

- Lowest regression risk
- No API contract changes
- Directly attacks the biggest startup memory sources
- Keeps a clean path to a later phase where modules can be split further if needed

**Rejected approach: large router/service split now**

- Could reduce memory further, but it is a wider refactor and raises regression risk.
- Better reserved for phase B if phase A still leaves the process too heavy.

**Implementation Notes**

- Introduce a small set of local helper imports inside endpoints that trigger export/report/related-notice/artifact-heavy behavior.
- Replace `from backend.services import ...` in `app.py` with concrete module imports only where those functions are actually used.
- Avoid loading `openpyxl.Workbook` at module import time if it is only used by rare export responses.
- Keep the existing auth-session performance branch changes intact.

**Testing Strategy**

- Add focused tests for any helper extraction that changes import boundaries.
- Run existing auth runtime tests to confirm login/session behavior is unchanged.
- Run targeted frontend auth session tests because the branch already contains session refresh changes.
- Run representative backend tests around export/tracker/admin paths touched by import boundary changes.

**Success Criteria**

- Hot startup paths do not import document parsing/export stacks unless those features are used.
- Backend process idle memory decreases materially from the current 1.4GB baseline.
- Common login/home/tracker flows remain green in tests.
- The next live server check should show swap usage stabilizing instead of continuous swap thrashing during normal console use.

**Phase B Trigger**

If phase A still leaves idle memory above target or swap pressure remains during normal use, move to phase B:

- split larger startup modules
- isolate tracker/export/report-heavy routes behind narrower modules
- further reduce shared globals and cache sizes
