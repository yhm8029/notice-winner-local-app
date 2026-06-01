# 00 Reference Index

- 문서 역할: 참고 문서 인덱스
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 현재 참고 문서가 어디에 있고, 어떤 정본 문서를 보조하는가
- 이 문서가 답하지 않는 질문: 구현 판단의 최종 기준, API/DB/상태의 최종 계약
- 상위 기준 문서: [../00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md), 각 `canonical` 문서

작성일: 2026-03-22  
대상 브랜치: `feature/phase2-auth-login`

## 1. 목적

`docs/reference/`는 정본 문서를 보조하는 참고 문서를 모아두는 위치다.
여기 있는 문서는 배경, 원천 자료, 예시, 검증 기준, 재구축 보조 자료를 제공할 수 있지만 `canonical` 문서를 덮어쓰지 못한다.

## 2. 하위 분류

- `source/`
  - 원천 기준, GUI parity 원본, 기존 재구축 기준서
- `contracts/`
  - API/DB/상태 전이/응답 예시 같은 부속 계약
- `operations/`
  - 운영 편의, phase 기준, 화면 패널 가이드, 운영 정책 보조 자료
- `rebuild/`
  - 재구축 골든 시나리오, 필드 매핑, UI 상태 매트릭스

## 3. 사용 원칙

1. 먼저 [../00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)에서 정본 문서를 확인한다.
2. 정본 문서를 읽은 뒤, 세부 배경이나 예시가 필요할 때만 reference 문서를 본다.
3. reference 문서와 canonical 문서가 충돌하면 항상 canonical 문서를 우선한다.

## 4. 대표 참고 문서

### 4.1 source

- 기능 원천: [source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md](./source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md)
- 설계 원천: [source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md](./source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md)
- 기술 원천: [source/TECHNICAL_SPEC_GUI_PARITY_KR.md](./source/TECHNICAL_SPEC_GUI_PARITY_KR.md)
- 원천 기준 참고서: [source/APP_REBUILD_SPEC_KR.md](./source/APP_REBUILD_SPEC_KR.md)

### 4.2 contracts

- API 계약 부속: [contracts/api-spec.md](./contracts/api-spec.md)
- DB 계약 부속: [contracts/db-schema.md](./contracts/db-schema.md)
- 상태 전이 부속: [contracts/job-lifecycle.md](./contracts/job-lifecycle.md)
- 요청/응답 예시: [contracts/request-response-examples.md](./contracts/request-response-examples.md)

### 4.3 operations

- 운영 정책 원천: [operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md](./operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md)
- 메일/SMTP 정책 부속: [operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](./operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md)
- 운영 편의 기능: [operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](./operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md)
- 화면/패널 참고: [operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt](./operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt)
- 검증 기준 참고: [operations/PHASE1_EQUIVALENCE_TEST_CASES_KR.md](./operations/PHASE1_EQUIVALENCE_TEST_CASES_KR.md)
- phase/완료판정 참고: [operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md](./operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md)

### 4.4 rebuild

- 재구축 골든 시나리오: [rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md](./rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md)
- 화면-API-DB 필드 매핑: [rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md](./rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md)
- UI 상태 매트릭스: [rebuild/UI_STATE_MATRIX_KR.md](./rebuild/UI_STATE_MATRIX_KR.md)

## 5. archive로 내려간 문서

아래 문서는 현재 기준보다 기록 보존 성격이 커서 `docs/archive/`로 이동했다.

- 산출물 후속 작업 메모: [../archive/notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md](../archive/notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md)
- 기술 보조 노트: [../archive/notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md](../archive/notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md)
- 정책 분리 참고: [../archive/notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md](../archive/notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md)
- handoff / review / experiment 문서 전체: [../archive/00_ARCHIVE_INDEX_KR.md](../archive/00_ARCHIVE_INDEX_KR.md)
