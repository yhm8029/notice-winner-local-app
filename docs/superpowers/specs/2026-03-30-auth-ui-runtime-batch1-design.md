# Auth UI Runtime Batch 1 Design

## Goal

Continue the current frontend modularization pattern by moving more auth/profile/invitation view logic out of `frontend/app.js` and into `frontend/auth-session-runtime.js`, without changing auth behavior.

This batch is intentionally frontend-only. Backend auth flow and API behavior stay unchanged.

## Scope

Target the auth shell and profile/invitation presentation layer in `frontend/app.js`.

In scope:

- `renderAuthUi()`
- `renderAuthInvitationPreview()`
- `renderProfileStatus()`
- `renderInvitationStatus()`
- profile dialog field-sync view logic inside `syncProfileDialogWithSession()`

Out of scope:

- auth API calls
- auth submit/reset/sign-out control flow
- invitation creation/revoke/accept API behavior
- backend auth runtime restructuring
- DOM selector or form field name changes

## Existing Direction

This branch already uses `frontend/*-runtime.js` modules for deterministic markup and view-model helpers.

`frontend/auth-session-runtime.js` already owns:

- auth session normalization
- invitation status view-model shaping
- invitation preview view-model shaping
- auth shell view-model shaping

The next consistent step is to expand that runtime so `frontend/app.js` becomes orchestration-only for auth UI, the same way other runtime seams were handled.

## Design

### Responsibility split

`frontend/auth-session-runtime.js` should own:

- auth status/presentation normalization helpers
- profile dialog form field view-model derivation
- invitation/profile status message view helpers
- invitation preview display shaping
- auth shell display shaping

`frontend/app.js` should keep:

- state mutation
- DOM writes
- event binding
- API calls
- dialog open/close lifecycle
- submit/reset/sign-out handlers

### Profile dialog handling

The runtime should expose a helper that derives the profile dialog display state from:

- current authenticated user
- invite-token context
- invitation preview status

That helper should provide:

- field values to render
- whether current-password input is required
- current-password placeholder text

`app.js` should remain responsible for writing those values into DOM inputs.

### Status message handling

The runtime should shape both invitation and profile status display consistently:

- normalized text
- visibility
- error-state flag

If one of these remains app-local for practical reasons, the interface still needs to follow the same runtime-first pattern already used elsewhere.

### Constraints

- Do not change auth mode switching behavior.
- Do not change any request payloads or endpoint calls.
- Do not change visible selector contracts or DOM ids/classes relied on by the page.
- Do not move event listeners into the runtime module.
- Keep runtime helpers deterministic and dependency-injected where needed.

## Testing Strategy

Add or extend a focused frontend runtime test file for auth-session runtime behavior.

The test coverage should include:

- auth UI view-model states for sign-in vs sign-up
- invitation preview rendering behavior
- profile dialog field-sync requirements
- invitation/profile status visibility and error flags
- app-side fallback behavior when the runtime helper is missing, if a new fallback seam is introduced

Verification should include:

- targeted `node --test` runtime suite
- `node --check` for touched frontend files
- existing auth-related frontend behavior remaining unchanged

## Risks And Mitigations

- Risk: auth shell copy or field requirements drift from current behavior
  - Mitigation: lock current behavior with focused view-model tests before moving logic
- Risk: profile dialog logic becomes split inconsistently between app and runtime
  - Mitigation: move only deterministic field derivation into runtime, keep DOM/event lifecycle in app
- Risk: invitation preview behavior changes for accepted/revoked/expired paths
  - Mitigation: explicitly test those states in the runtime suite

## Success Criteria

- `frontend/app.js` becomes smaller around auth/profile presentation logic.
- `frontend/auth-session-runtime.js` clearly owns more of the auth UI view-model logic.
- Auth shell, invitation preview, and profile dialog behavior remain unchanged.
- Selector contracts and API calls remain unchanged.
- Targeted frontend verification passes cleanly.
