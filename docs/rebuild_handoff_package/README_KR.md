# 재구축 전달 보조 패키지

- 생성일: 2026-04-30
- 생성 방식: local `in_memory` repository + synthetic collect mode
- 운영 secret 사용 여부: 사용하지 않음. 추출 프로세스에서 Supabase 관련 환경변수를 빈 값으로 덮어씀.
- 기준 문서: `docs/spec/REBUILD_RFP_FINAL_SPEC_KR.md`

## 구성

1. `api-samples/`: 주요 API 요청/응답 JSON
2. `sample-data/`: synthetic 샘플 데이터 발췌
3. `screenshots/`: 로컬 synthetic 화면 캡처
4. `checklists/REBUILD_ACCEPTANCE_CHECKLIST_KR.md`: 외부 개발사 검수 체크리스트
5. `user-flow/USER_FLOW_RECORDING_SCRIPT_KR.md`: 5~10분 사용 흐름 녹화 대본

## API 샘플 추출 상태

```json
{
  "00_health": {
    "status": 200,
    "path": "/health"
  },
  "01_dashboard_summary": {
    "status": 200,
    "path": "/api/dashboard/summary"
  },
  "02_home_bootstrap": {
    "status": 200,
    "path": "/api/home-bootstrap"
  },
  "03_tracker_entries": {
    "status": 200,
    "path": "/api/tracker-entries"
  },
  "04_sales_claims": {
    "status": 200,
    "path": "/api/sales-claims"
  },
  "05_sales_claim_overview": {
    "status": 200,
    "path": "/api/sales-claims/overview"
  },
  "06_sales_claim_summary_by_user": {
    "status": 200,
    "path": "/api/sales-claims/summary-by-user"
  },
  "07_admin_organization_bootstrap": {
    "status": 503,
    "path": "/api/admin/organization-panel-bootstrap"
  },
  "09_tracker_missing_report": {
    "status": 200,
    "path": "/api/tracker-entries/missing-report"
  }
}
```

## 스크린샷 추출 상태

```json
[
  {
    "path": "docs\\rebuild_handoff_package\\screenshots\\01_user_home.png",
    "exists": true,
    "bytes": 616513
  },
  {
    "path": "docs\\rebuild_handoff_package\\screenshots\\02_admin_project_status.png",
    "exists": true,
    "bytes": 1281443
  },
  {
    "path": "docs\\rebuild_handoff_package\\screenshots\\04_login_invite_preview_shell.png",
    "exists": true,
    "bytes": 435898
  },
  {
    "path": "docs\\rebuild_handoff_package\\user-flow\\current_app_flow.webm",
    "exists": true,
    "bytes": 1448725
  }
]
```

## 전달 권장 순서

외부 개발사 또는 새 구현팀에는 아래 순서로 전달한다.

1. `docs/spec/REBUILD_RFP_FINAL_SPEC_KR.md`
2. `docs/spec/REBUILD_FUNCTIONAL_SPEC_KR.md`
3. `docs/spec/REBUILD_UI_UX_SPEC_KR.md`
4. `docs/spec/REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md`
5. `docs/spec/REBUILD_OPERATIONS_SECURITY_SPEC_KR.md`
6. `docs/spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md`
7. `docs/spec/IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md`
8. 본 패키지 전체

## 제한

이 패키지는 synthetic/in-memory 기준 보조 자료다. 실제 운영 데이터, secret, 기존 소스 코드, 운영 DB dump를 포함하지 않는다.
