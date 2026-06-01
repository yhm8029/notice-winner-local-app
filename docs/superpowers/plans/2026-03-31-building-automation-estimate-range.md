# Building Automation Estimate Range Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the derived building automation estimate to `1.5%~2.0%` of the current construction cost basis and format it as `x.xx억원~y.yy억원` across tracker/export and sales-claim flows.

**Architecture:** Keep the existing source basis and only change the estimate generation and text formatting logic. Update tests at the native tracker/export layer and the sales-claim parsing layer so the same range text is accepted and exported consistently.

**Tech Stack:** Python, existing tracker export logic, workbook export pipeline, pytest/unittest

---

## File Structure

- Modify: `backend/services/native_tracker_backend.py`
  - Update the derived building automation estimate calculation and text formatting.
- Modify: `backend/services/native_export_backend.py`
  - Keep generated export rows aligned if this layer formats or forwards the estimate field directly.
- Modify: `backend/sales_claims.py`
  - Ensure the range parser continues to accept the new `x.xx억원~y.yy억원` format without the old suffix words.
- Modify: `tests/test_native_tracker_backend.py`
  - Replace old expectations like `최대 ...억원 예상`.
- Modify: `tests/test_native_export_backend.py`
  - Replace old expectations where export rows carry the derived estimate text.
- Modify: `tests/test_native_export_schedule_fields.py`
  - Update schedule/export expectations for the estimate field.
- Modify: `tests/test_sales_claims.py`
  - Confirm the parser and aggregate logic still accept the new range string.

### Task 1: Update Failing Expectations First

**Files:**
- Modify: `tests/test_native_tracker_backend.py`
- Modify: `tests/test_native_export_backend.py`
- Modify: `tests/test_native_export_schedule_fields.py`
- Modify: `tests/test_sales_claims.py`

- [ ] **Step 1: Change native tracker expectations to the new range text**

Update assertions that currently expect strings such as `최대 2.81억원 예상` or `최대 3.65억원 예상` so they expect `1.41억원~1.87억원`-style output with two decimals.

Example target assertions:

```python
self.assertEqual(rows[0]["building_automation_estimated_amount"], "1.41억원~1.87억원")
```

- [ ] **Step 2: Update export-layer expectations**

Replace old expected text in export-related tests with the same two-decimal range format.

Example:

```python
self.assertEqual(out_row["building_automation_estimated_amount"], "1.41억원~1.87억원")
```

- [ ] **Step 3: Keep sales claim parsing expectations aligned**

Use the new text style in sales claim parsing tests.

Example:

```python
claim = SalesClaim.create(
    tracker_entry_id=tracker_entry_id,
    organization_id=organization_id,
    user_id=user_id,
    estimated_amount_text="1.50억원~2.00억원",
)
assert claim.estimated_amount_low_krw is not None
assert claim.estimated_amount_high_krw is not None
```

- [ ] **Step 4: Run the focused tests to confirm they fail before implementation**

Run:

```powershell
python -m pytest `
  tests/test_native_tracker_backend.py `
  tests/test_native_export_backend.py `
  tests/test_native_export_schedule_fields.py `
  tests/test_sales_claims.py -q
```

Expected: failures on old estimate text expectations.

### Task 2: Change Estimate Generation

**Files:**
- Modify: `backend/services/native_tracker_backend.py`
- Modify: `backend/services/native_export_backend.py`

- [ ] **Step 1: Find the current derived percentage path**

Locate the helper that currently turns a construction cost basis into strings like `최대 ...억원 예상`.

Expected logic shape:

```python
estimated_text = build_building_automation_estimated_amount(...)
```

- [ ] **Step 2: Change the percentage rule to 1.5%~2.0%**

Implement:

```python
low_amount = base_amount * Decimal("0.015")
high_amount = base_amount * Decimal("0.020")
```

and keep the same existing source-basis selection.

- [ ] **Step 3: Change the text formatter**

Format the output as:

```python
f"{low_eok:.2f}억원~{high_eok:.2f}억원"
```

with no `최대` and no `예상`.

- [ ] **Step 4: Ensure export rows continue to forward the same field unchanged**

If export code separately formats this field, make it pass through the new string verbatim rather than rebuilding the old phrase.

### Task 3: Keep Sales Claim Parsing Compatible

**Files:**
- Modify: `backend/sales_claims.py`
- Modify: `tests/test_sales_claims.py`

- [ ] **Step 1: Confirm the existing range parser accepts the new string**

Current range parsing should still match `x.xx억원~y.yy억원`. If it depends on old suffix words, narrow the regex so it accepts the plain range text.

Example accepted value:

```python
"1.50억원~2.00억원"
```

- [ ] **Step 2: Preserve single-value parsing**

Do not break existing single-value strings like:

```python
"12억원"
```

- [ ] **Step 3: Run focused sales-claim tests**

Run:

```powershell
python -m pytest tests/test_sales_claims.py -q
```

Expected: all sales claim parsing tests pass.

### Task 4: Verify End-to-End Focused Regression

**Files:**
- Modify: none

- [ ] **Step 1: Run the complete focused regression set**

Run:

```powershell
python -m pytest `
  tests/test_native_tracker_backend.py `
  tests/test_native_export_backend.py `
  tests/test_native_export_schedule_fields.py `
  tests/test_sales_claims.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Spot-check the exact new output text**

Verify at least one representative assertion path now produces:

```text
1.41억원~1.87억원
```

and no remaining expectation contains `최대` or `예상` for this field.

- [ ] **Step 3: Commit**

Run:

```powershell
git add `
  backend/services/native_tracker_backend.py `
  backend/services/native_export_backend.py `
  backend/sales_claims.py `
  tests/test_native_tracker_backend.py `
  tests/test_native_export_backend.py `
  tests/test_native_export_schedule_fields.py `
  tests/test_sales_claims.py
git commit -m "feat: narrow building automation estimate range"
```

Expected: one commit containing the calculation and regression updates.
