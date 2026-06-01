# Artifact And Backend Seam Modularization Design

## Goal

Continue the existing related-notice-search modularization pattern without changing behavior.

This batch proceeds in two steps:

1. Frontend artifact rendering extraction
2. Backend tracker/artifact seam extraction

The intent is to keep `frontend/app.js` and `backend/api/app.py` moving toward orchestration-only roles while preserving current selector contracts, API responses, and runtime fallbacks.

## Scope

### Step 1: Frontend artifact rendering

Target the artifact list and preview rendering path in `frontend/app.js`.

In scope:

- `renderArtifactsList()`
- `buildArtifactSectionMarkup()`
- `renderArtifactCardMarkup()`
- artifact empty-state message rendering seam where appropriate
- preview markup delegation that already flows through `artifact-runtime.js`

Out of scope:

- artifact fetch/load lifecycle
- selected run state transitions
- preview caching policy
- tracker workbook warm/download flow

### Step 2: Backend tracker/artifact seam

After the frontend batch is stable, extract one cohesive tracker/artifact response-assembly block from `backend/api/app.py` into `backend/services/*_backend.py`.

Preferred target:

- tracker/artifact response shaping and selection helpers

Avoid in this batch:

- auth/session restructuring
- route layout changes
- repository contract changes
- database behavior changes

## Design Principles

- Preserve the current runtime/seam pattern already used in this branch.
- Keep `app.js` responsible for state, fetches, and event wiring.
- Keep runtime modules focused on deterministic markup helpers and formatting helpers.
- Keep `backend/api/app.py` responsible for routing and HTTP concerns only.
- Move pure shaping/selection logic into backend service modules.
- Maintain app-side fallbacks where runtime helpers are optional.

## Frontend Design

### New responsibility split

`frontend/artifact-runtime.js` should own:

- artifact section markup helpers
- artifact card markup helpers
- empty-state message formatting helpers that are pure and dependency-injected

`frontend/app.js` should keep:

- state reads/writes
- DOM event binding
- API calls
- preview toggle lifecycle
- cache population

### Constraints

- Existing `data-preview-artifact-id` and related selectors must not change.
- The rendered open/closed preview behavior must remain unchanged.
- Runtime helpers must remain safe to call with injected helper functions only.
- If a runtime helper is absent, `app.js` must not crash.

## Backend Design

### New responsibility split

Create or extend a dedicated backend service module for the selected tracker/artifact seam.

That backend module should own:

- deterministic response shaping
- artifact selection logic
- tracker-context helper logic

`backend/api/app.py` should keep:

- route registration
- request parsing
- auth and permission checks
- HTTP response/error translation

### Constraints

- No endpoint path changes
- No response schema changes
- No storage/backend selection changes
- Existing tests must continue to describe externally visible behavior

## Testing Strategy

### Frontend

- Add or extend focused runtime tests for artifact section/card markup.
- Add fallback coverage when runtime helpers are unavailable.
- Preserve selector-contract assertions for click targets and preview toggles.
- Run `node --test` for affected frontend runtime suites.
- Run `node --check` for touched frontend files.

### Backend

- Add or extend unit tests around the extracted backend seam.
- Keep API-level tests covering unchanged endpoint behavior.
- Run targeted Python unit tests for touched backend modules.

## Risks And Mitigations

- Risk: selector drift between runtime and app fallback
  - Mitigation: parity-style tests on key markup paths
- Risk: over-extracting stateful code into runtime modules
  - Mitigation: keep fetch/event/caching logic in `app.js`
- Risk: backend seam extraction accidentally changing HTTP behavior
  - Mitigation: keep request/response translation in `backend/api/app.py` and verify with targeted API tests

## Success Criteria

- Artifact rendering code in `frontend/app.js` is materially smaller and more orchestration-focused.
- One additional tracker/artifact seam is removed from `backend/api/app.py`.
- No selector contract regressions.
- No API behavior regressions.
- Targeted frontend and backend verification passes cleanly.
