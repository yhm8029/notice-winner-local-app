# User Mode Shared Google Sheets Design

**Date**

- 2026-04-19

**Goal**

Show the same `프로젝트 현황 / 설계리스트 / 발주예정 / ...` Google Sheets-backed navigation in both 사용자모드 and 운영자모드, while keeping all Google Sheets sync controls and operator-only wording hidden from 사용자모드.

**Decision Summary**

- Reuse the existing admin Google Sheets tab model for both modes instead of duplicating a second user-only implementation.
- Change the 사용자모드 default landing screen to `프로젝트 현황`.
- Keep Google Sheets content read-only in both modes.
- Preserve all existing 운영자 기능, but render sync controls and operator-facing status copy only in 운영자모드.
- Avoid any backend API contract changes for this task.

## Background

- The frontend already builds dynamic Google Sheets tabs from bootstrap data in [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js).
- Today those tabs are effectively treated as 운영자 화면 because the tab bar, Google Sheets panel, and related route behavior are tied to `uiMode === "admin"`.
- The user wants the same visible tabs and sheet tables in 사용자모드 too.
- The user explicitly does **not** want the following to appear in 사용자모드:
  - `admin` style wording
  - `Google Sheets read-only view`
  - `Google Sheets sync_status=...`
  - the `Google Sheets 동기화` button
- The user wants 운영자모드 left unchanged.

## Scope

### In Scope

- showing the existing project status and Google Sheets tabs in 사용자모드
- changing 사용자모드 default landing to `프로젝트 현황`
- reusing the same tab navigation and sheet payload rendering in both modes
- hiding operator-only Google Sheets controls and copy from 사용자모드
- keeping filtering and tab switching available in 사용자모드
- preserving existing 운영자-only management panels and actions

### Out of Scope

- changing backend auth or authorization rules
- changing Google Sheets sync cadence or snapshot schema
- adding editing actions in 사용자모드
- redesigning the existing 운영자 panels outside the shared tab/navigation decision

## Approaches Considered

1. Share the same Google Sheets navigation and display layer across both modes
   - Keep one source of truth for tabs and payload rendering.
   - Add mode-aware rules only for controls, copy, and route defaults.
   - Pros: lowest long-term maintenance, consistent UI, least duplication.
   - Cons: requires careful untangling of `admin`-only display assumptions in the frontend.
   - Recommended.

2. Build a second user-only copy of the Google Sheets tab screen
   - Duplicate the existing admin Google Sheets panel into a separate user-mode surface.
   - Pros: smaller immediate risk to the current admin flow.
   - Cons: duplicated logic, duplicated tests, higher future drift risk.

3. Keep the current user-mode home and embed only sheet content blocks
   - Show some of the same data in user mode without sharing the full tab structure.
   - Pros: smallest surface change.
   - Cons: does not match the requested “same as 운영자모드” behavior.

## Recommended Design

Use one shared navigation/rendering path for `프로젝트 현황` and Google Sheets tabs, with mode-specific visibility rules for operator controls and wording.

### Shared Tab Model

Both modes should use the same resolved tab list:

- `프로젝트 현황`
- dynamically resolved Google Sheets tabs such as:
  - `설계리스트`
  - `발주예정`
  - other synced sheet tabs

The existing `adminGoogleSheetTabs` bootstrap data remains the source of truth.

### User Mode Default

When the app enters 사용자모드:

- default route should land on `프로젝트 현황`
- the shared tab/navigation strip should still be visible
- users can switch into the synced Google Sheets tabs from there

This changes the current “general home first” assumption for 사용자모드.

### Operator-Only UI

Keep these visible only in 운영자모드:

- `Google Sheets 동기화` button
- sync follow-up feedback such as `sync_status=queued`
- operator-oriented empty/overview copy
- explicit `admin` wording
- `Google Sheets read-only view` subtitle copy

### Shared Read-Only Sheet Table

In both modes:

- Google Sheets table content remains read-only
- tab navigation works
- filters work
- sheet payload rendering stays identical

In 사용자모드:

- no sync action is shown
- no sync feedback is shown
- the panel title/subtitle should use business-facing labels rather than operator-facing explanatory text

## UX Rules

### User Mode

- first visible screen after login is `프로젝트 현황`
- top tab/navigation strip is visible
- selecting `설계리스트`, `발주예정`, or other sheet tabs loads the same table view as 운영자모드
- no operator-only messaging should appear

### Admin Mode

- current behavior remains intact
- same tabs and table behavior remain available
- sync button and status feedback remain visible
- admin-only panels stay admin-only

## Routing Rules

### Shared Routes

The frontend should treat the project status / Google Sheets route family as accessible in both modes for display purposes.

This means:

- route parsing should no longer force these screens into `admin` mode only
- user mode should be able to stay in `uiMode === "user"` while still resolving the shared tab keys
- `admin_tab` style state can still be reused internally as the tab selector if that is the least risky path

### Mode Preservation

When a 사용자모드 user opens a shared tab:

- do not silently flip to 운영자모드
- keep `uiMode === "user"`
- only share the navigation/display shell

This is the most important behavioral distinction. Shared view does not mean shared operator mode.

## Architecture Changes

### Frontend State

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)

- separate “shared project status / Google Sheets navigation is visible” from “admin mode is active”
- update user-mode default routing so the first screen resolves to `프로젝트 현황`
- allow shared tab resolution and panel rendering in user mode
- gate sync button, sync feedback, and operator wording on `uiMode === "admin"`

### Runtime

[`frontend/admin-google-sheets-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/admin-google-sheets-runtime.js)

- no major structural change required
- continue rendering the shared table view used by both modes
- only mode-specific title/subtitle/feedback text should be controlled by `app.js`

### Markup / Copy

[`frontend/index.html`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/index.html)

- keep existing operator button markup available for admin mode
- user mode should not expose those controls once the render rules are updated

## Risks And Mitigations

### Risk: user mode accidentally gains operator actions

Mitigation:

- keep all action bindings and sync controls explicitly gated by `uiMode === "admin"`
- verify no sync button is rendered in user mode

### Risk: route logic accidentally forces user mode into admin mode

Mitigation:

- make shared route visibility independent from admin mode
- add tests that verify user mode remains `user` while showing shared tabs

### Risk: existing admin behavior regresses

Mitigation:

- preserve admin-mode tests
- add explicit regression coverage for admin sync button visibility and existing sheet rendering

## Test Plan

Add or update frontend tests to verify:

1. 사용자모드 default landing is `프로젝트 현황`
2. 사용자모드 shows the shared tab strip and Google Sheets tabs
3. 사용자모드 can open synced sheet tabs without switching to 운영자모드
4. 사용자모드 does not render:
   - sync button
   - sync feedback text
   - operator subtitle copy
5. 운영자모드 still renders those controls and messages
6. existing Google Sheets table rendering and filtering continue to work in both modes

## Success Criteria

- 사용자모드 enters on `프로젝트 현황`
- 사용자모드 and 운영자모드 share the same `프로젝트 현황 / 설계리스트 / 발주예정 / ...` navigation
- 사용자모드 can read the same Google Sheets content with filters and tab switching
- 사용자모드 never shows operator-only sync controls or operator-facing copy
- 운영자모드 behavior stays unchanged
