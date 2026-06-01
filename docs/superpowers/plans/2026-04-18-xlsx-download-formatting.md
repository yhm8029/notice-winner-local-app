# XLSX Download Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply a shared XLSX formatting pass so all downloaded workbooks use font size 10, row-2 filters, and `yyyy-mm-dd` notice dates.

**Architecture:** Keep workbook generation paths intact and add one shared formatting helper in `backend/services/artifact_files.py`. Route both template-based tracker downloads and the code-built missing-report workbook through that helper before bytes are returned.

**Tech Stack:** Python, FastAPI, openpyxl, pytest/unittest

---

## File Map

- Modify: `backend/services/artifact_files.py`
  - add shared workbook formatting helper
  - call it from tracker workbook generation
- Modify: `backend/api/app.py`
  - expose and use the shared formatting helper for missing report xlsx
- Modify: `tests/test_artifact_files.py`
  - add tracker workbook formatting regression coverage
- Modify: `tests/api/test_phase1_api.py`
  - add missing report xlsx formatting coverage

### Task 1: Lock Tracker Workbook Formatting With Tests

**Files:**
- Modify: `tests/test_artifact_files.py`
- Modify: `backend/services/artifact_files.py`

- [ ] **Step 1: Write the failing tracker workbook formatting tests**
- [ ] **Step 2: Run targeted tests and confirm failure**
- [ ] **Step 3: Add the shared formatting helper and wire tracker workbooks through it**
- [ ] **Step 4: Re-run targeted tests and confirm pass**
- [ ] **Step 5: Commit**

### Task 2: Apply Shared Formatting To Missing Report XLSX

**Files:**
- Modify: `tests/api/test_phase1_api.py`
- Modify: `backend/api/app.py`
- Modify: `backend/services/artifact_files.py`

- [ ] **Step 1: Write the failing missing report formatting test**
- [ ] **Step 2: Run targeted API test and confirm failure**
- [ ] **Step 3: Reuse the shared formatting helper in missing report xlsx generation**
- [ ] **Step 4: Re-run targeted API test and confirm pass**
- [ ] **Step 5: Commit**

## Final Verification

- [ ] Run: `pytest tests/test_artifact_files.py tests/api/test_phase1_api.py -q`
- [ ] Confirm all formatting regressions pass
- [ ] Push updated `main`
