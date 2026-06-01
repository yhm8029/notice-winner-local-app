# Request / Response Examples

- 문서 역할: 요청/응답 예시 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 현재 API 계약의 대표 예시는 어떤 형태인가
- 상위 기준 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)
- 충돌 시 우선 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)

- 예시는 현재 GUI 파라미터와 child run 기반 tracker export 구조를 따른다.
- `tracker_entries` 응답은 effective value 기준이다.
- `PATCH /api/tracker-entries/{entry_id}`는 한 번에 한 field만 수정한다.

## 1. 실행 생성

### Request
```http
POST /api/runs
Content-Type: application/json
```

```json
{
  "run_type": "project_tracker",
  "params": {
    "start_date": "20250101",
    "end_date": "20250630",
    "contract_date_hint": "20250715",
    "bid_no": "",
    "notice_title": "기계공사",
    "demand_org": "",
    "rows_per_page": 100,
    "max_pages": 3,
    "api_scope": "construction"
  },
  "advanced_options": {}
}
```

### Response
```json
{
  "id": "run_uuid",
  "status": "queued",
  "run_type": "project_tracker",
  "parent_run_id": null,
  "created_at": "2026-03-12T10:00:00+09:00"
}
```

## 2. 실행 상세 조회

### Response
```json
{
  "id": "run_uuid",
  "status": "running",
  "run_type": "project_tracker",
  "parent_run_id": null,
  "progress_stage": "rescan",
  "progress_current": 42,
  "progress_total": 180,
  "cancel_requested": false,
  "params": {
    "start_date": "20250101",
    "end_date": "20250630",
    "notice_title": "기계공사"
  },
  "summary": {},
  "error": {},
  "created_at": "2026-03-12T10:00:00+09:00",
  "started_at": "2026-03-12T10:00:03+09:00",
  "finished_at": null
}
```

## 3. 로그 조회

### Response
```json
{
  "items": [
    {
      "id": 1,
      "level": "info",
      "stage": "finalize",
      "message": "project_tracker finished successfully",
      "created_at": "2026-03-12T10:00:20+09:00",
      "meta": {}
    }
  ],
  "next_cursor": 1
}
```

## 4. artifact 조회

### 부모 run Response
```json
{
  "items": [
    {
      "id": "artifact_uuid",
      "artifact_type": "winner_csv",
      "file_name": "project_tracker_rows.csv",
      "mime_type": "text/csv",
      "size_bytes": 52341,
      "checksum": "sha256_here",
      "meta": {
        "rows": 2
      },
      "download_url": "/api/artifacts/artifact_uuid/download",
      "download_url_expires_in": 600
    }
  ]
}
```

## 5. 실행 취소

### Response
```json
{
  "id": "run_uuid",
  "status": "running",
  "cancel_requested": true
}
```

## 6. 트래커 export 실행

### Request
```http
POST /api/runs/run_uuid/tracker-export
```

### Response
```json
{
  "id": "tracker_run_uuid",
  "parent_run_id": "run_uuid",
  "run_type": "tracker_export",
  "status": "queued",
  "created_at": "2026-03-12T10:25:00+09:00"
}
```

### tracker_export child run 조회
```json
{
  "id": "tracker_run_uuid",
  "status": "success",
  "run_type": "tracker_export",
  "parent_run_id": "run_uuid",
  "progress_stage": "finalize",
  "progress_current": 2,
  "progress_total": 2,
  "cancel_requested": false,
  "params": {
    "source_run_id": "run_uuid"
  },
  "summary": {
    "output": {
      "tracker_entry_rows": 2,
      "entry_keys": [
        "r25bk00555367|000|project-name",
        "r25bk00555367|001|project-name-follow-up"
      ],
      "tracking_excel_generated": true,
      "tracking_excel_file_name": "project_tracking.xlsx"
    }
  },
  "error": {}
}
```

### tracker_export child run artifact 조회
```json
{
  "items": [
    {
      "id": "tracker_artifact_uuid",
      "artifact_type": "tracking_excel",
      "file_name": "project_tracking.xlsx",
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "size_bytes": 84321,
      "checksum": "sha256_here",
      "meta": {
        "rows": 2
      },
      "download_url": "/api/artifacts/tracker_artifact_uuid/download",
      "download_url_expires_in": 600
    }
  ]
}
```

## 7. 트래커 엔트리 목록 조회

### Request
```http
GET /api/tracker-entries?edited_only=true&page=1&page_size=20
```

### Response
```json
{
  "items": [
    {
      "id": "tracker_entry_uuid",
      "source_run_id": "run_uuid",
      "source_tracker_run_id": "tracker_run_uuid",
      "entry_key": "r25bk00555367|000|project-name",
      "sheet_name": "Sheet1",
      "section_name": "facility_cost",
      "row_no": 12,
      "source_bid_no": "R25BK00555367",
      "source_bid_ord": "000",
      "source_project_name_norm": "project-name",
      "project_name": "Project Name A",
      "gross_area_scale": "12 floors / 14200 sqm",
      "construction_cost": "18500000000",
      "demand_org_name": "Korea Facilities Agency",
      "demand_contact": "Architecture Team Kim",
      "client_location": "Seoul Jung-gu",
      "site_location_1": "Seoul Jung-gu Eulji-ro",
      "site_location_2": "Seoul Jung-gu Supyo-dong",
      "architect_office": "Garam Architects",
      "construction_start_date": "2026-05-01",
      "last_checked_date": "2026-03-12",
      "progress_note": "Phone verification complete",
      "notice_date": "2026-03-11",
      "manager_name": "Kim Younghee",
      "building_automation_estimated_amount": "350000000",
      "overridden_fields": [
        "project_name",
        "progress_note"
      ],
      "last_edited_at": "2026-03-12T14:05:00+09:00",
      "last_edited_by": null,
      "last_edited_by_label": "hyunmo",
      "created_at": "2026-03-12T14:00:00+09:00",
      "updated_at": "2026-03-12T14:05:00+09:00"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

## 8. 트래커 엔트리 수정

### Request
```http
PATCH /api/tracker-entries/tracker_entry_uuid
Content-Type: application/json
```

```json
{
  "field_name": "project_name",
  "value": "Project Name Final",
  "actor_user_id": null,
  "actor_label": "hyunmo",
  "change_source": "web"
}
```

### Response
```json
{
  "changed": true,
  "entry": {
    "id": "tracker_entry_uuid",
    "source_run_id": "run_uuid",
    "source_tracker_run_id": "tracker_run_uuid",
    "entry_key": "r25bk00555367|000|project-name",
    "sheet_name": "Sheet1",
    "section_name": "facility_cost",
    "row_no": 12,
    "source_bid_no": "R25BK00555367",
    "source_bid_ord": "000",
    "source_project_name_norm": "project-name",
    "project_name": "Project Name Final",
    "gross_area_scale": "12 floors / 14200 sqm",
    "construction_cost": "18500000000",
    "demand_org_name": "Korea Facilities Agency",
    "demand_contact": "Architecture Team Kim",
    "client_location": "Seoul Jung-gu",
    "site_location_1": "Seoul Jung-gu Eulji-ro",
    "site_location_2": "Seoul Jung-gu Supyo-dong",
    "architect_office": "Garam Architects",
    "construction_start_date": "2026-05-01",
    "last_checked_date": "2026-03-12",
    "progress_note": "Phone verification complete",
    "notice_date": "2026-03-11",
    "manager_name": "Kim Younghee",
    "building_automation_estimated_amount": "350000000",
    "overridden_fields": [
      "project_name",
      "progress_note"
    ],
    "last_edited_at": "2026-03-12T14:30:00+09:00",
    "last_edited_by": null,
    "last_edited_by_label": "hyunmo",
    "created_at": "2026-03-12T14:00:00+09:00",
    "updated_at": "2026-03-12T14:30:00+09:00"
  },
  "audit_log": {
    "id": 3,
    "field_name": "project_name",
    "old_value": "Project Name A",
    "new_value": "Project Name Final",
    "actor_user_id": null,
    "actor_label": "hyunmo",
    "change_source": "web",
    "created_at": "2026-03-12T14:30:00+09:00"
  }
}
```

### override 제거 예시
```json
{
  "field_name": "project_name",
  "value": null,
  "actor_label": "hyunmo",
  "change_source": "web"
}
```

> `value = null`이면 override를 제거하고 source value로 되돌린다.

## 9. 트래커 엔트리 감사 로그 조회

### Request
```http
GET /api/tracker-entries/tracker_entry_uuid/audit-logs?limit=2
```

### Response
```json
{
  "items": [
    {
      "id": 3,
      "field_name": "project_name",
      "old_value": "Project Name A",
      "new_value": "Project Name Final",
      "actor_user_id": null,
      "actor_label": "hyunmo",
      "change_source": "web",
      "created_at": "2026-03-12T14:30:00+09:00"
    },
    {
      "id": 2,
      "field_name": "progress_note",
      "old_value": "",
      "new_value": "Phone verification complete",
      "actor_user_id": null,
      "actor_label": "hyunmo",
      "change_source": "web",
      "created_at": "2026-03-12T14:05:00+09:00"
    }
  ],
  "next_cursor": 2
}
```

## 10. 검증 실패

### Response `400`
```json
{
  "error": {
    "code": "validation_error",
    "message": "start_date must be YYYYMMDD"
  }
}
```

> validation error는 run을 생성하지 않고 요청 단계에서 반환한다.

