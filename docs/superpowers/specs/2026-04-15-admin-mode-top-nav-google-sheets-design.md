# Admin Mode Top Navigation With Google Sheet Tabs Design

**Goal**

Add an admin-only top navigation to the SPMS web app so operators can switch between the existing project status view and four new Google Sheet-backed tabs without changing user-mode behavior.

## Background

- The current frontend is a single-page app built from [`frontend/index.html`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/index.html) and [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js).
- The app already distinguishes between admin/operator and user views through `uiMode` and existing mode-toggle controls.
- The user wants the current SPMS admin page to remain the default `프로젝트 현황` view.
- Four new admin tabs should be added beside it:
  - `설계리스트`
  - `발주예정`
  - `로스트`
  - `대리점 리스트`
- The first release should render those four tabs as embedded Google Sheet views based on provided sheet sources. Later, those tabs may evolve into app-native data views fed by continuously synced Google Sheet data.

## Scope

### In Scope

- admin-only top horizontal navigation
- URL-backed admin tab state
- keeping the existing admin project-status screen as the default `프로젝트 현황` tab
- adding four new admin tabs that render Google Sheet embeds
- preserving current user-mode rendering and behavior
- minimal frontend changes in the current single-page architecture

### Out of Scope

- changing user-mode layout or navigation
- redesigning the existing `프로젝트 현황` business logic
- building Google Sheet ingestion or sync jobs
- transforming Google Sheet data into native SPMS tables in this iteration
- backend API changes unless a small frontend-serving adjustment is unavoidable

## Requirements

### Functional

1. When the app is in admin mode, a top horizontal navigation bar appears above the main admin content.
2. The navigation contains exactly five tabs:
   - `프로젝트 현황`
   - `설계리스트`
   - `발주예정`
   - `로스트`
   - `대리점 리스트`
3. `프로젝트 현황` is the default admin tab and shows the current SPMS admin content as-is.
4. The other four tabs each show a Google Sheet embed view inside the main content area.
5. The selected admin tab is reflected in the URL through a query parameter such as `admin_tab`.
6. Refreshing the page preserves the selected admin tab.
7. User mode does not show the new admin navigation and continues to behave exactly as it does now.

### Non-Functional

- prefer the smallest safe diff
- avoid broad refactors of the existing admin page
- do not disturb existing admin data-loading and render paths for `프로젝트 현황`
- keep the new tab system easy to replace later with native data views

## Approaches Considered

1. Inline admin tab switching with URL-backed query state
   - Keep the app as one page.
   - Add a lightweight tab key such as `admin_tab`.
   - Show either the existing admin body or a Google Sheet embed container based on that key.
   - Pros: minimal diff, lowest regression risk, fits the current architecture.
   - Cons: `app.js` remains responsible for another UI branch.
   - Recommended.

2. Inline admin tab switching without URL state
   - Store the selected tab only in frontend state.
   - Pros: slightly simpler implementation.
   - Cons: refresh resets the selected tab, links cannot preserve context.

3. Separate routes or pages per admin section
   - Treat each tab as a standalone page.
   - Pros: clearer long-term separation.
   - Cons: unnecessary complexity for the current single-page frontend, higher regression risk, larger diff.

## Recommended Design

Use inline admin tab switching with URL-backed query state.

### Admin Navigation Model

- Introduce a small admin-tab model in the frontend, for example:
  - `project-status`
  - `design-list`
  - `planned-orders`
  - `lost`
  - `agency-list`
- Resolve the active tab from the URL query parameter on load.
- If the query parameter is missing or invalid, fall back to `project-status`.
- Render the top navigation only when the app is in admin mode.

### Content Switching

- `project-status` renders the existing SPMS admin content path with no change to the underlying business logic.
- The other four tab keys render a common embed-panel path that swaps only:
  - title
  - active tab state
  - embed URL/source
- This keeps the current admin content and the new Google Sheet views isolated from each other.

### URL Contract

- Use a query parameter such as `admin_tab`.
- Example values:
  - `?admin_tab=project-status`
  - `?admin_tab=design-list`
  - `?admin_tab=planned-orders`
  - `?admin_tab=lost`
  - `?admin_tab=agency-list`
- Tab clicks update the URL without requiring a full page navigation.
- On refresh, the app reads the query parameter and restores the same admin tab.

### Google Sheet Embed Boundary

- Each new tab should be configured through a simple mapping object:
  - label
  - tab key
  - embed source or embed URL
- In the first release, the embed source is treated as a display-only integration.
- The render boundary should be explicit so that later replacement is simple:
  - current release: iframe/embed container
  - future release: app-native list/table driven by synced sheet data

## Architecture

### Existing Admin View Preservation

- The existing admin dashboard, forms, run status, tracker panels, and related content should remain in place behind the `프로젝트 현황` tab.
- No attempt should be made in this change to split or rewrite the existing admin feature modules.
- The new navigation should wrap or sit above the existing admin content rather than restructuring its internals.

### New Frontend Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)

- define admin tab metadata
- read and validate the active admin tab from the URL
- update the URL when an admin tab is selected
- render admin navigation only for admin mode
- switch between:
  - existing admin main content
  - Google Sheet embed content

[`frontend/index.html`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/index.html)

- if needed, add a dedicated mount point for the admin top navigation or embed container
- preserve the existing user-mode and admin-mode shells

[`frontend/styles.css`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/styles.css)

- add styles for the admin top navigation
- add styles for the Google Sheet embed content area
- ensure the result works on desktop and mobile widths

## Data Model

The frontend should maintain a small configuration object for the five admin tabs.

Suggested fields:

- `key`
- `label`
- `type`
  - `existing`
  - `embed`
- `embedUrl` for Google Sheet-backed tabs

This keeps tab registration explicit and keeps future migration to native views low-risk.

## Error Handling

- If `admin_tab` is invalid, default to `project-status`.
- If an embed URL is missing for a configured sheet tab, show a stable admin-facing empty/error panel rather than breaking the page.
- If a Google Sheet refuses embedding or loads poorly, the failure should stay contained within the embed panel and not affect the `프로젝트 현황` tab.

## Testing

1. Verify user mode still renders exactly as before and does not show the admin navigation.
2. Verify admin mode defaults to `프로젝트 현황`.
3. Verify the current SPMS admin content still appears under `프로젝트 현황`.
4. Verify each of the four new tabs renders the correct Google Sheet embed panel.
5. Verify tab clicks update the `admin_tab` query parameter.
6. Verify refresh preserves the selected tab.
7. Verify invalid `admin_tab` values fall back cleanly to `프로젝트 현황`.
8. Verify switching between admin and user modes hides/shows the navigation correctly.

## Risks

- Adding the top navigation may disturb the current hero/layout spacing if inserted at the wrong point in the DOM.
- If tab switching reuses the wrong render path, existing admin data loading for `프로젝트 현황` could rerun unnecessarily or render inconsistently.
- Google Sheet embedding may have browser or permission constraints, so the UI should handle unavailable embeds gracefully.

## Success Criteria

- Admin mode shows a top horizontal tab bar with the requested five tabs.
- `프로젝트 현황` preserves the existing SPMS admin page content.
- The other four tabs open as Google Sheet embed views.
- URL-backed tab state survives refresh.
- User mode remains unchanged.
