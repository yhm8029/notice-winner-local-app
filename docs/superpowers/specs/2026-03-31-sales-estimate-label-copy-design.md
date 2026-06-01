# Sales Estimate Label Copy Design

## Goal

Update the sales/tracker card label for building automation estimate text so the UI matches the new estimate rule.

## Scope

- Replace `빌딩자동제어 추정금액(공사비 최대 3%)`
- With `빌딩자동제어 추정금액(공사비의 1.5~2%)`

## Affected UI

- Sales project cards
- Tracker entry cards
- `app.js` fallback markup used when runtime helpers are unavailable

## Non-Goals

- No calculation changes
- No backend/API changes
- No data migration

## Verification

- Update affected frontend string assertions
- Run focused frontend tests and syntax checks
