# Auth Runtime Orchestration Batch 2 Design

## Goal

Continue the current backend modularization pattern by moving the remaining session/profile orchestration logic out of `backend/api/auth_runtime.py` into a focused backend service module, without changing auth API behavior.

This batch is intentionally limited to orchestration. Existing invitation, profile lookup/write, local bootstrap, session cookie, and response-shaping helper backends stay in place.

## Scope

Target the large public orchestration functions in `backend/api/auth_runtime.py`.

In scope:

- `sign_in_with_password()`
- `sign_up_console_user()`
- `send_password_reset_email()`
- `ensure_fresh_session_payload()`
- `build_session_response()`
- `refresh_auth_session()`
- `update_console_user_profile()`

Out of scope:

- invitation read/write backend restructuring
- profile lookup/write backend restructuring
- cookie codec changes
- auth request transport changes
- API route changes
- schema or environment-variable changes

## Existing Direction

This branch already splits auth runtime support into focused backends:

- invitation read, write, and session helpers
- profile lookup and write helpers
- local bootstrap helpers
- session cookie helpers
- session response shaping

`backend/api/auth_runtime.py` still holds a large amount of decision-making orchestration that composes those helpers. The next consistent step is to extract that orchestration into a dedicated backend service file while keeping `auth_runtime.py` as the public facade used by the API layer.

## Design

### Responsibility split

Create a new backend service module dedicated to auth session/profile orchestration.

The new backend module should own:

- sign-in orchestration
- sign-up orchestration
- password reset orchestration
- session refresh decision flow
- session status response refresh flow
- console profile update orchestration

`backend/api/auth_runtime.py` should keep:

- public exported functions with the existing names
- configuration and constants
- request/response transport helpers
- low-level auth/rest helper wrappers already used across the file
- thin delegation glue into the new backend module

### Interface style

The new backend module should stay deterministic and dependency-injected, matching the existing service-backend pattern in this repo.

That means the extracted functions should receive:

- primitive inputs such as email, password, invite token, request host, and session payload
- injected helpers for auth requests, bootstrap fallback, invitation acceptance, profile mutation, cookie IO, refresh timing, and time reads
- the existing `AuthRuntimeError` class passed as a dependency where needed

The new backend must not import `auth_runtime.py` to avoid cycles.

### Sign-in and sign-up handling

The sign-in and sign-up orchestration should preserve the current behavior exactly:

- local bootstrap fallback behavior
- pending invitation resolution by email
- invitation/email match enforcement
- accepted invitation auto-accept path on sign-in
- bootstrap account special handling
- member local-user ensure path

Only the orchestration moves. Existing helper ownership remains unchanged.

### Session refresh handling

The extracted session refresh logic should cover both protected-request refresh and session-status refresh.

It should keep the current distinctions:

- protected requests raise `401 auth_required` and clear the cookie when refresh cannot be completed
- session-status checks return a logged-out payload with the current expiration message when refresh fails
- cookie mutation remains app/runtime-layer controlled through injected `set_auth_session_cookie` and `clear_auth_session_cookie`

### Profile update handling

The extracted profile-update orchestration should preserve the current split:

- local bootstrap sessions update the local bootstrap password store and local projection only
- regular sessions verify current password, update Supabase auth profile/password, sync local profile, and rebuild session payload
- invite-backed password setup remains allowed only through the existing invitation-session helper

### File structure

Recommended new module:

- `backend/services/auth_session_orchestration_backend.py`

This file should stay focused on orchestration only. If a helper inside it grows into a separate concern, that should be a later batch, not part of this one.

## Testing Strategy

Keep this batch test-first.

Coverage should be extended in `tests/test_auth_runtime.py` first, before moving production code, to lock current behavior for:

- sign-in local bootstrap fallback
- bootstrap sign-up fallback
- invitation token acceptance path on sign-in
- session refresh success/failure for both `ensure_fresh_session_payload()` and `build_session_response()`
- profile update behavior for local bootstrap and regular Supabase sessions

Add a focused backend unit test file for the new backend module if that improves isolation:

- `tests/test_auth_session_orchestration_backend.py`

If a dedicated backend test file is added, `tests/test_auth_runtime.py` should still retain thin facade coverage proving delegation preserves public behavior.

Verification should include:

- targeted Python unit tests for auth runtime and the new backend module
- existing auth-related tests that cover invitation/session/profile paths

## Risks And Mitigations

- Risk: auth session refresh semantics drift between protected requests and status checks
  - Mitigation: lock both paths with explicit tests before extraction
- Risk: bootstrap fallback handling changes during refactor
  - Mitigation: keep bootstrap-specific behavior under dedicated tests and inject the exact fallback helpers
- Risk: `auth_runtime.py` becomes a second orchestration layer instead of a thin facade
  - Mitigation: move decision branches into the new backend module and leave only argument wiring in the facade

## Success Criteria

- `backend/api/auth_runtime.py` is materially smaller around session/profile orchestration.
- A new focused backend module clearly owns auth session/profile orchestration.
- Public auth behavior, errors, response payloads, and cookie semantics remain unchanged.
- Tests prove both the new backend module and the `auth_runtime.py` facade still preserve current behavior.
