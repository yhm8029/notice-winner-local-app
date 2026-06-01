# Building Automation Estimate Range Design

## Goal

Change the generated `building_automation_estimated_amount` value so it uses a fixed range of `1.5%~2.0%` of the current construction cost basis, and present the text as `x.xx억원~y.yy억원` without the words `최대` or `예상`.

## Scope

- Keep the existing source basis for the estimate calculation
- Change only the derived building automation estimate rule and text formatting
- Apply the new format to the tracker row value that feeds:
  - tracker workbook export
  - sales claim estimate text flows
  - any generated tracker/export rows using this derived value
- Do not change unrelated extraction logic for cost, area, contact, architect office, or schedule date

## Recommended Approach

Update the central estimate generation logic instead of patching export-only output. This keeps the tracker row, sales claim estimate text, and workbook exports consistent.

Why this approach:

- the field is already reused by multiple outputs
- export-only formatting would create drift between UI and downloads
- the change remains narrow because it only touches the derived building automation estimate field

## Calculation Rule

- low estimate: `construction_cost_basis * 0.015`
- high estimate: `construction_cost_basis * 0.020`
- format both values in `억원`
- round/display to two decimal places
- final string format:
  - `x.xx억원~y.yy억원`

## Affected Areas

- estimate generation for tracker rows
- workbook export value population through the existing field
- sales claim parsing/tests that expect the old `...억원 추정` style

## Risks And Controls

- Range parsing regression:
  keep the existing `low~high억원` parsing path covered by tests.
- Formatting drift:
  update tests that currently expect `최대 ...억원 예상`.
- Scope creep:
  do not touch the broader extraction rules for cost and notice parsing outside the derived estimate field.

## Out Of Scope

- changing the construction cost extraction source
- changing manual overrides
- changing other tracker/export columns
