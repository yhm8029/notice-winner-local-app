# Tracker Export Education Office Sheet Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make tracker export downloads keep `전체` with all rows, keep ordinary region sheets for non-education issuers only, and add top-level education-office sheets such as `서울교육청` and `경남교육청`.

**Architecture:** Extend the existing workbook sheet builder in `backend/services/artifact_files.py` instead of replacing it. Add a small issuer-classification layer that detects `교육청` and `교육지원청`, normalizes them to a top-level region education-office sheet, and then feeds ordinary and education rows into separate sheet groups while leaving `전체` untouched.

**Tech Stack:** Python, `openpyxl`, pytest-style tests in `tests/test_artifact_files.py`

---

## File Map

- Modify: `backend/services/artifact_files.py:190-324`
  - Keep workbook byte generation entrypoints unchanged.
  - Add education-office classification helpers next to the existing region grouping helpers.
  - Update `_build_tracking_workbook(..., split_region_sheets=True)` to build `전체`, ordinary region sheets, and education-office sheets in a deterministic order.
- Modify: `tests/test_artifact_files.py:119-260`
  - Keep existing workbook-region tests passing.
  - Add focused tests for education-office sheet normalization and mixed workbook output.

### Task 1: Add Education Office Sheet Classification Helpers

**Files:**
- Modify: `backend/services/artifact_files.py:292-324`
- Test: `tests/test_artifact_files.py:119-170`

- [ ] **Step 1: Write the failing helper classification test**

Add this test near the existing region split test block in `tests/test_artifact_files.py`:

```python
def test_derive_tracking_education_office_sheet_name_collapses_support_offices_to_top_level_region() -> None:
    assert artifact_files._derive_tracking_education_office_sheet_name(  # type: ignore[attr-defined]
        {"demand_org_name": "경상남도교육청 경상남도창녕교육지원청"}
    ) == "경남교육청"
    assert artifact_files._derive_tracking_education_office_sheet_name(  # type: ignore[attr-defined]
        {"demand_org_name": "서울특별시강서양천교육지원청"}
    ) == "서울교육청"
    assert artifact_files._derive_tracking_education_office_sheet_name(  # type: ignore[attr-defined]
        {"demand_org_name": "경상남도 의령군"}
    ) == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_artifact_files.py::test_derive_tracking_education_office_sheet_name_collapses_support_offices_to_top_level_region -q`

Expected: FAIL with `AttributeError` because `_derive_tracking_education_office_sheet_name` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add these helpers in `backend/services/artifact_files.py` below `_group_tracking_rows_by_region(...)` and above `_make_tracking_sheet_title(...)`:

```python
TRACKING_REGION_SHORT_NAMES = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "제주특별자치도": "제주",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
}


def _iter_tracking_issuer_texts(row: dict[str, Any]) -> list[str]:
    return [
        str(row.get("demand_org_name") or "").strip(),
        str(row.get("client_location") or "").strip(),
    ]


def _is_tracking_education_office_text(text: str) -> bool:
    normalized = str(text or "").strip()
    return "교육청" in normalized or "교육지원청" in normalized


def _short_tracking_region_name(region_name: str) -> str:
    normalized = str(region_name or "").strip()
    return TRACKING_REGION_SHORT_NAMES.get(normalized, normalized)


def _derive_tracking_education_office_sheet_name(row: dict[str, Any]) -> str:
    for text in _iter_tracking_issuer_texts(row):
        if not _is_tracking_education_office_text(text):
            continue
        for canonical, aliases in TRACKER_REGION_ALIASES.items():
            for alias in aliases:
                if _tracking_region_alias_matches(text=text, canonical=canonical, alias=alias):
                    short_region = _short_tracking_region_name(canonical)
                    return f"{short_region}교육청" if short_region else ""
    return ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_artifact_files.py::test_derive_tracking_education_office_sheet_name_collapses_support_offices_to_top_level_region -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/artifact_files.py tests/test_artifact_files.py
git commit -m "test: classify tracker education office sheets"
```

### Task 2: Split Workbook Sheets Into Total, Ordinary Regions, and Education Offices

**Files:**
- Modify: `backend/services/artifact_files.py:238-324`
- Test: `tests/test_artifact_files.py:119-210`

- [ ] **Step 1: Write the failing mixed workbook split test**

Add this test near `test_build_tracking_download_workbook_splits_region_sheets(...)` in `tests/test_artifact_files.py`:

```python
def test_build_tracking_download_workbook_splits_ordinary_and_education_office_sheets(monkeypatch, tmp_path: Path):
    template = tmp_path / "template.xlsx"
    _write_template(template)
    monkeypatch.setenv("TRACKER_TEMPLATE_PATH", str(template))

    payload = artifact_files.build_tracking_download_workbook_bytes(
        rows=[
            {
                "project_name": "서울시청 별관",
                "demand_org_name": "서울특별시",
                "site_location_1": "서울특별시",
            },
            {
                "project_name": "의령 복합센터",
                "demand_org_name": "경상남도 의령군",
                "site_location_1": "경상남도",
            },
            {
                "project_name": "창원 농업센터",
                "demand_org_name": "경상남도 창원시 농업기술센터",
                "site_location_1": "경상남도",
            },
            {
                "project_name": "서울 북부 교육지원청 청사",
                "demand_org_name": "서울특별시교육청 서울특별시북부교육지원청",
                "client_location": "서울특별시교육청 서울특별시북부교육지원청",
                "site_location_1": "서울특별시",
            },
            {
                "project_name": "창녕 교육지원청 청사",
                "demand_org_name": "경상남도교육청 경상남도창녕교육지원청",
                "client_location": "경상남도교육청 경상남도창녕교육지원청",
                "site_location_1": "경상남도",
            },
        ]
    )

    output = tmp_path / "download_mixed.xlsx"
    output.write_bytes(payload)
    wb = load_workbook(output)

    assert wb.sheetnames == ["전체", "서울", "경남", "서울교육청", "경남교육청"]
    assert [wb["전체"]["B3"].value, wb["전체"]["B4"].value, wb["전체"]["B5"].value, wb["전체"]["B6"].value, wb["전체"]["B7"].value] == [
        "서울시청 별관",
        "의령 복합센터",
        "창원 농업센터",
        "서울 북부 교육지원청 청사",
        "창녕 교육지원청 청사",
    ]
    assert wb["서울"]["B3"].value == "서울시청 별관"
    assert wb["서울"]["B4"].value in (None, "")
    assert wb["경남"]["B3"].value == "의령 복합센터"
    assert wb["경남"]["B4"].value == "창원 농업센터"
    assert wb["경남"]["B5"].value in (None, "")
    assert wb["서울교육청"]["B3"].value == "서울 북부 교육지원청 청사"
    assert wb["경남교육청"]["B3"].value == "창녕 교육지원청 청사"

    wb.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_artifact_files.py::test_build_tracking_download_workbook_splits_ordinary_and_education_office_sheets -q`

Expected: FAIL because the current workbook builder only creates region sheets and mixes education-office rows into ordinary region sheets.

- [ ] **Step 3: Write minimal implementation**

Update `_build_tracking_workbook(...)` and add a download grouping helper in `backend/services/artifact_files.py`:

```python
def _group_tracking_rows_for_download_sheets(
    rows: list[dict[str, Any]]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    ordinary_grouped: dict[str, list[dict[str, Any]]] = {}
    education_grouped: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        education_sheet_name = _derive_tracking_education_office_sheet_name(row)
        if education_sheet_name:
            education_grouped.setdefault(education_sheet_name, []).append(row)
            continue

        region_name = _derive_tracking_region_name(row)
        if region_name:
            ordinary_grouped.setdefault(region_name, []).append(row)

    region_order = {name: index for index, name in enumerate(TRACKER_REGION_ALIASES.keys())}
    ordinary_sorted = {
        region_name: ordinary_grouped[region_name]
        for region_name in sorted(ordinary_grouped.keys(), key=lambda item: (region_order.get(item, 999), item))
    }
    education_sorted = {
        sheet_name: education_grouped[sheet_name]
        for sheet_name in sorted(
            education_grouped.keys(),
            key=lambda item: (region_order.get(next(
                canonical for canonical, short_name in TRACKING_REGION_SHORT_NAMES.items()
                if f"{short_name}교육청" == item
            ), 999), item),
        )
    }
    return ordinary_sorted, education_sorted


def _build_tracking_workbook(*, rows: list[dict[str, Any]], split_region_sheets: bool = False):
    template_path = resolve_tracker_template_path()
    wb = load_workbook(template_path)
    base_ws = wb[wb.sheetnames[0]]
    _populate_tracking_sheet(base_ws, rows=rows)
    if not split_region_sheets:
        return wb

    ordinary_grouped, education_grouped = _group_tracking_rows_for_download_sheets(rows)
    if not ordinary_grouped and not education_grouped:
        return wb

    used_titles: set[str] = set()
    base_ws.title = _make_tracking_sheet_title("전체", used_titles)
    for region_name, region_rows in ordinary_grouped.items():
        ws = wb.copy_worksheet(base_ws)
        ws.title = _make_tracking_sheet_title(_short_tracking_region_name(region_name), used_titles)
        _populate_tracking_sheet(ws, rows=region_rows)
    for sheet_name, sheet_rows in education_grouped.items():
        ws = wb.copy_worksheet(base_ws)
        ws.title = _make_tracking_sheet_title(sheet_name, used_titles)
        _populate_tracking_sheet(ws, rows=sheet_rows)
    return wb
```

If the `next(...)` expression feels too implicit while implementing, replace it with a small helper that converts `서울교육청` back to its canonical region before sorting. Keep the final behavior identical.

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_artifact_files.py::test_build_tracking_download_workbook_splits_region_sheets tests/test_artifact_files.py::test_build_tracking_download_workbook_splits_ordinary_and_education_office_sheets -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/services/artifact_files.py tests/test_artifact_files.py
git commit -m "feat: split tracker download sheets by education office"
```

### Task 3: Lock In Fallback and Regression Coverage

**Files:**
- Modify: `tests/test_artifact_files.py:170-260`
- Modify: `backend/services/artifact_files.py:292-340`

- [ ] **Step 1: Write the failing fallback test for education detection from client location**

Add this test in `tests/test_artifact_files.py` after the helper-classification test:

```python
def test_derive_tracking_education_office_sheet_name_falls_back_to_client_location() -> None:
    assert artifact_files._derive_tracking_education_office_sheet_name(  # type: ignore[attr-defined]
        {
            "demand_org_name": "",
            "client_location": "부산광역시해운대교육지원청",
        }
    ) == "부산교육청"
```

- [ ] **Step 2: Run test to verify it fails if helper only reads one field**

Run: `pytest tests/test_artifact_files.py::test_derive_tracking_education_office_sheet_name_falls_back_to_client_location -q`

Expected: FAIL if the helper only checks `demand_org_name` or stops too early.

- [ ] **Step 3: Write minimal implementation**

Confirm `_iter_tracking_issuer_texts(...)` keeps `demand_org_name` first and `client_location` second, and skips blanks:

```python
def _iter_tracking_issuer_texts(row: dict[str, Any]) -> list[str]:
    ordered = (
        str(row.get("demand_org_name") or "").strip(),
        str(row.get("client_location") or "").strip(),
    )
    return [value for value in ordered if value]
```

If the implementation from Task 1 already matches this behavior, do not add extra logic. Keep the diff minimal.

- [ ] **Step 4: Run targeted regression tests**

Run: `pytest tests/test_artifact_files.py -q`

Expected: PASS for the full workbook helper suite, including existing region split and site-city normalization tests.

- [ ] **Step 5: Commit**

```bash
git add backend/services/artifact_files.py tests/test_artifact_files.py
git commit -m "test: cover tracker education office workbook fallbacks"
```

## Final Verification

- [ ] Run the focused workbook regression suite:

```bash
pytest tests/test_artifact_files.py -q
```

Expected: all tests in `tests/test_artifact_files.py` pass.

- [ ] Check the final diff is limited to workbook export grouping:

```bash
git diff --stat HEAD~3..HEAD
```

Expected: only `backend/services/artifact_files.py` and `tests/test_artifact_files.py` changed during implementation commits.

## Self-Review

- Spec coverage: the tasks cover `전체` retention, ordinary region filtering, top-level education-office normalization, standalone `교육지원청` handling, and targeted regression coverage.
- Placeholder scan: no `TBD`, `TODO`, or vague “handle appropriately” steps remain.
- Type consistency: all tasks use the same helper names: `_iter_tracking_issuer_texts`, `_derive_tracking_education_office_sheet_name`, and `_group_tracking_rows_for_download_sheets`.
