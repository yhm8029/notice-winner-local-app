# Platform Admin Account Creation Design

## Goal

Add a platform-admin-only account creation flow that lets operators create console accounts directly from the admin console, while keeping the implementation ready for future password-policy upgrades.

This is a controlled operational feature, not an open self-sign-up expansion.

## Scope

In scope:

- platform-admin-only account creation from the admin console
- backend API for direct account creation
- direct initial-password entry by the platform admin
- audit logging for account creation and follow-up admin actions
- feature-flag gating so the feature can ship dark
- minimal admin UI for create/list/status actions

Out of scope:

- public self-sign-up changes
- org-admin self-service account creation
- billing or plan automation changes
- bulk import
- account deletion hard-removal
- broad auth refactors unrelated to this flow

## Existing Direction

The current auth flow already supports:

- invitation-based account onboarding
- admin-side Supabase user creation during sign-up orchestration
- organization membership and audit behavior
- admin-mode operational UI panels in the web console

That means the safest next step is not a new parallel auth system. The safer path is to add one focused platform-admin account creation path that reuses the existing auth and membership model, then gate it behind a feature flag until it is verified.

## Approaches

### 1. Direct account creation with admin-entered initial password

Platform admins create the auth user, local profile, and organization membership directly. The platform admin enters the initial password at creation time, and the created account can sign in immediately.

Pros:

- no dependency on email delivery
- strongest operational control
- least day-to-day admin friction
- consistent audit trail

Cons:

- requires careful handling so admin-entered passwords never leak through UI, logs, or audit payloads
- still needs a small persistence extension for admin provenance and future password-policy compatibility

### 2. Keep invitations but improve admin UX

Platform admins continue issuing invitations, but the UI becomes easier to operate and exposes copyable invite links and better status feedback.

Pros:

- smaller implementation
- closer to current behavior

Cons:

- keeps email and invite-token operational failure modes
- does not solve the original operator request for direct ID creation

## Decision

Choose approach 1.

The operator requirement is controlled account issuance by platform admins. Invitation-only UX still leaves the same delivery and activation friction in place. A direct creation flow with admin-entered initial passwords matches the current operational need while still allowing a later upgrade to generated passwords and forced first-login rotation.

## Design

### Access model

Only `platform_admin` can use the direct account creation API and UI.

`org_admin` keeps the current invitation-based behavior and does not gain direct account creation in this batch. This avoids widening the write surface in production while the new flow proves stable.

### Feature gate

Add a dedicated environment flag such as `ENABLE_PLATFORM_ADMIN_ACCOUNT_CREATION`.

Behavior:

- default `off`
- when `off`, the new UI stays hidden and the API returns a clear forbidden or disabled response
- when `on`, only authenticated `platform_admin` sessions can access the feature

This allows production deployment without immediate operator exposure.

In practical terms, this is a safety switch. The code can be deployed first, but the button and API stay hidden until the operator is ready to enable them.

### Account creation flow

Platform admin submits:

- email
- display name
- organization
- role
- initial password

Backend flow:

1. validate actor is `platform_admin`
2. validate target role is allowed
3. validate the provided initial password against the current password rules
4. create Supabase auth user directly
5. create or sync the local user/profile projection
6. create the organization membership
7. mark the account as immediately usable
8. append audit logs for account creation
9. return account summary plus current status

The API must reject duplicate active accounts and duplicate memberships explicitly with stable error codes.

### Current account state

Accounts created through this flow are immediately usable.

Required semantics:

- initial state is `active`
- no forced password change is required in this batch
- existing sign-in and session behavior stays unchanged for newly created accounts

The admin response model should still expose explicit account lifecycle fields so a later password-policy upgrade does not require a second API redesign.

### Data model

Add the smallest schema extension needed to express admin provenance and future password-policy state.

Preferred direction:

- extend the auth profile or local user projection with:
  - `account_status`
  - `created_by_user_id`
  - `created_at` if not already available in the relevant projection
  - an optional field reserved for future first-login password policy such as `password_setup_mode` or `force_password_change`

If an existing profile table already carries adjacent lifecycle state, extend that table instead of creating a new one.

Do not introduce a second account-state source of truth.

### Password-policy forward compatibility

The current UI accepts an admin-entered initial password.

The design should still leave room for two future upgrades:

- backend-generated temporary passwords
- forced first-login password change

That means the create-account API and persistence model should be shaped so a later change can switch password issuance mode or enable a forced-rotation flag without replacing the whole admin feature.

### Admin UI

Add a small platform-admin-only account management panel in the existing admin area.

Initial UI scope:

- create account form
- recent accounts list with role, organization, and status
- status badge for `active` and `inactive`
- targeted actions:
  - reset password
  - deactivate account

Do not add bulk editing, deletion, or org-admin exposure in this batch.

### Audit and observability

Audit events are required for:

- account created
- password reset issued by admin
- account deactivated

Operational errors during audit insertion should be best-effort and must not block the primary admin action, consistent with the repo's conservative operational pattern.

## File Direction

Likely touched areas:

- `backend/api/app.py`
- `backend/api/auth_runtime.py`
- `backend/api/schemas.py`
- `backend/services/auth_session_orchestration_backend.py`
- existing auth profile/write backend modules if they already own lifecycle fields
- `frontend/app.js`
- `frontend/auth-session-runtime.js`
- `frontend/org-admin-runtime.js`
- `frontend/console-data-runtime.js`
- `tests/test_auth_runtime.py`
- targeted backend and frontend runtime tests
- `supabase/migrations/*`

The implementation should stay surgical. Extend existing auth and admin seams instead of introducing a parallel admin account subsystem.

## Testing Strategy

Backend coverage should lock:

- feature flag off path
- platform admin create success path
- duplicate account rejection
- duplicate membership rejection
- immediate sign-in eligibility for created accounts
- non-platform-admin rejection
- deactivate and admin-password-reset actions

Frontend coverage should lock:

- admin panel hidden when feature flag or role is unavailable
- create form render and submission state
- account status badge rendering

Verification should prefer targeted test runs over broad suite execution.

## Rollout Plan

1. implement behind `ENABLE_PLATFORM_ADMIN_ACCOUNT_CREATION=0`
2. merge and deploy with the flag still off
3. apply the database migration
4. enable the flag only for controlled operator validation
5. create one internal test account
6. validate direct sign-in, password reset, and account status transitions
7. expand normal operator usage only after the validation passes

This rollout keeps production impact low because code can ship dark before the write path is exposed.

## Risks And Mitigations

- Risk: new write path creates inconsistent auth user and membership state
  - Mitigation: keep the flow sequential, fail clearly, and reuse existing profile/membership helpers instead of duplicating logic
- Risk: future password-policy changes require a second rewrite
  - Mitigation: keep explicit lifecycle fields in the response and reserve a forward-compatible password-policy field in persistence
- Risk: production exposure before operators are ready
  - Mitigation: feature flag default off and platform-admin-only access
- Risk: admin-entered passwords are handled carelessly in UI or logs
  - Mitigation: never echo stored passwords back after creation and never persist raw passwords in audit payloads

## Success Criteria

- platform admins can create a console account directly without invitation email delivery
- created accounts can sign in immediately with the admin-provided password
- the feature remains invisible in production until explicitly enabled
- account lifecycle actions are auditable
- the implementation leaves a clean path for future generated-password and forced-password-change behavior
