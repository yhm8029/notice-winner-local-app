# Tracker Export Site Location Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 엑셀 전반의 현장 위치 헤더를 `현장위치(시도)` / `현장위치(시군구)`로 명확히 바꾸고, 비어 있는 시군구를 발주처 위치에서 보정한다.

**Architecture:** 변경 범위는 `backend/services/artifact_files.py`의 템플릿 헤더 해석과 workbook 렌더링에 한정한다. 내부 데이터 모델은 유지하고, 엑셀 작성 시점에만 표기와 보정 로직을 적용한다.

**Tech Stack:** Python, openpyxl, pytest

---

### Task 1: Add Failing Tests For Header Labels And Site City Fallback

**Files:**
- Modify: `tests/test_artifact_files.py`
- Test: `tests/test_artifact_files.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_header_columns_accepts_split_site_location_labels():
    ...

def test_build_tracking_workbook_fills_site_city_from_client_location_when_missing():
    ...

def test_build_tracking_workbook_keeps_existing_site_city():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_artifact_files.py -q`
Expected: FAIL in the new header/fallback assertions

- [ ] **Step 3: Write minimal implementation**

```python
mapping = {
    "site_loc_region": ("현장위치(시도)", "현장위치"),
    "site_loc_city": ("현장위치(시군구)", "현장위치"),
}

site_city = row.get("site_location_2") or _split_region_city_from_address(...)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/Scripts/python.exe -m pytest tests/test_artifact_files.py -q`
Expected: PASS

- [ ] **Step 5: Review touched export call sites**

Check: `backend/services/artifact_files.py`
Expected: both tracker artifact generation and download xlsx generation still flow through the same workbook builder
