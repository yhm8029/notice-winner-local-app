# Tracker Export Education Office Sheet Split Design

## Goal

Tracker export workbook download should separate ordinary local-government issuers from education-office issuers.

The workbook should keep one `전체` sheet with every row, then create:

- ordinary region sheets such as `서울`, `인천`, `부산`, `경남`, `경북`
- education-office sheets such as `서울교육청`, `경남교육청`

Ordinary region sheets must contain only non-education issuers for that region.
Education-office sheets must contain only education-office issuers for that education office's top-level region.

## Requested Behavior

- `전체` contains every exported tracker row without filtering.
- `서울` contains only ordinary Seoul issuers.
- `서울교육청` contains notices from `서울특별시교육청` and Seoul-related `교육지원청`.
- `경남` contains only ordinary Gyeongnam issuers such as `경상남도 의령군`, `경상남도 창원시`, and related centers/divisions.
- `경남교육청` contains notices from `경상남도교육청` and Gyeongnam-related `교육지원청`.

Examples:

- `경상남도 의령군` -> `전체`, `경남`
- `경상남도 창원시 농업기술센터` -> `전체`, `경남`
- `경상남도교육청 경상남도창녕교육지원청` -> `전체`, `경남교육청`
- `서울특별시강서양천교육지원청` -> `전체`, `서울교육청`

## Non-Goals

- No change to CSV export behavior.
- No change to tracker row normalization outside workbook sheet grouping.
- No duplication of education-office rows into ordinary region sheets.

## Current State

`backend/services/artifact_files.py` currently builds:

- one base workbook sheet
- optional split sheets by inferred region via `_group_tracking_rows_by_region`

This logic does not distinguish education-office issuers from ordinary local-government issuers, so both kinds can appear together in the same region sheet.

## Design Options Considered

### Option 1: Add education-office grouping on top of current region grouping

Create `전체`, then build ordinary region sheets with education-office rows removed, and build education-office sheets separately.

Pros:

- Minimal diff against existing workbook generation
- Preserves current region grouping behavior for ordinary issuers
- Matches the requested workbook layout exactly

Cons:

- Adds another grouping axis to workbook generation

### Option 2: Duplicate education-office rows into both region and education-office sheets

Pros:

- Easier for users browsing only region sheets

Cons:

- Keeps the original "mixed rows" problem in region sheets
- Creates row duplication and possible operator confusion

### Option 3: Replace region grouping entirely with custom issuer buckets

Pros:

- Very explicit output contract

Cons:

- Larger rewrite
- Higher regression risk for existing region sheet behavior

## Chosen Design

Use Option 1.

Keep the current region split model, then add a second grouping pass for education-office issuers.

## Classification Rules

### 1. Source fields

Use issuer-like fields in this order:

1. `demand_org_name`
2. `client_location`

The first field that allows a confident classification wins.

### 2. Education-office issuer detection

Treat a row as education-office-related when the chosen issuer text contains either:

- `교육청`
- `교육지원청`

This includes:

- direct metropolitan/provincial education offices
- strings that combine top-level education office and subordinate education support office
- standalone education support office names

### 3. Education-office top-level grouping

Normalize education-office rows to a top-level education-office bucket:

- `서울특별시교육청`, `서울특별시북부교육지원청`, `서울특별시교육청 서울특별시북부교육지원청` -> `서울교육청`
- `경상남도교육청`, `경상남도창녕교육지원청`, `경상남도교육청 경상남도창녕교육지원청` -> `경남교육청`

The grouping key should be derived from the official top-level region already detectable in the codebase, then rendered as a shortened sheet name:

- `서울특별시` -> `서울교육청`
- `부산광역시` -> `부산교육청`
- `경상남도` -> `경남교육청`
- `전북특별자치도` -> `전북교육청`

### 4. Ordinary region grouping

Rows that are not classified as education-office rows continue to use the existing region grouping behavior.

Examples:

- `서울특별시`, `서울특별시 강동구`, `서울시 산하 사업소` -> `서울`
- `경상남도`, `경상남도 의령군`, `경상남도 창원시 농업기술센터` -> `경남`

### 5. Fallback behavior

If a row looks like education-office text but the top-level region cannot be determined confidently:

- keep the row in `전체`
- do not place it in an education-office sheet
- allow the existing ordinary region grouping only if region inference remains valid from current logic

This avoids dropping rows while keeping grouping conservative.

## Workbook Structure

Generation order should be:

1. Base sheet renamed to `전체`
2. Ordinary region sheets in the existing region order, excluding education-office rows
3. Education-office sheets in official region order, only for regions that actually have rows

Expected example:

- `전체`
- `서울`
- `인천`
- `부산`
- `경남`
- `경북`
- `서울교육청`
- `경남교육청`

Exact sheet presence depends on whether rows exist for that bucket.

## Implementation Plan Boundary

Primary file:

- `backend/services/artifact_files.py`

Tests:

- extend `tests/test_artifact_files.py`

Likely implementation helpers:

- classify issuer rows into ordinary vs education-office buckets
- infer top-level education-office region from issuer text
- build short education-office sheet titles
- keep `전체` sheet unfiltered

## Validation

Add workbook-level tests that verify:

1. `전체` keeps all rows
2. ordinary region sheets exclude education-office rows
3. education-office sheets include both direct education offices and subordinate education support offices
4. combined strings like `경상남도교육청 경상남도창녕교육지원청` normalize to `경남교육청`
5. standalone strings like `서울특별시강서양천교육지원청` normalize to `서울교육청`

## Risks

- False positives if non-school issuers happen to contain education keywords unexpectedly
- Inconsistent issuer source fields between `demand_org_name` and `client_location`
- Sheet ordering drift if education-office sheets are inserted inconsistently

## Risk Mitigation

- Reuse existing official region normalization where possible
- Keep detection conservative and scoped to explicit `교육청` or `교육지원청`
- Add targeted tests for mixed region and education-office examples from the reported export
