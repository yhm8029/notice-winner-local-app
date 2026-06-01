# 00 Canonical Index

- 문서 역할: 문서 체계 헌법
- 정본 여부: `canonical`
- 이 문서가 답하는 질문: 어떤 문서가 현재 재구축 기준인가, 문서 충돌 시 무엇을 우선해야 하는가
- 이 문서가 답하지 않는 질문: 개별 기능 상세, API 필드 상세, DB 컬럼 상세
- 상위 기준 문서: 없음
- 충돌 시 우선 문서: 본 문서 자신

작성일: 2026-03-22  
대상 브랜치: `feature/phase2-auth-login`  
목적: 문서 체계를 `canonical / reference / archive`로 고정하고, 재구축 기준 문서와 참고 문서를 명확히 분리한다.

2026-04-30 현재, `origin/main`의 실제 구현 기준 재구축 문서는 [spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md)가 선언하는 `현재 구현 기준 재구축 v2` 세트를 우선한다. 기존 2026-03-22 정본 세트와 v2 세트가 충돌하면 v2 세트를 우선한다.

## 1. 이 문서의 역할

이 문서는 `docs/` 전체의 해석 우선순위를 정의하는 최상위 인덱스다.
개별 문서 메타는 [01_DOCUMENT_METADATA_REGISTRY_KR.md](./01_DOCUMENT_METADATA_REGISTRY_KR.md)에서 중앙 관리한다.

이 문서가 답하는 질문:
- 어떤 문서가 현재 구현/재구축의 기준 문서인가
- 어떤 문서는 참고용이고 어떤 문서는 과거 기록 보존용인가
- 문서 간 충돌이 날 때 무엇을 우선해야 하는가
- 현재 문서 개편을 어떤 순서로 진행해야 하는가

이 문서가 답하지 않는 질문:
- 개별 기능의 상세 요구사항
- API 필드별 세부 계약
- DB 컬럼의 모든 정의
- 특정 화면의 세부 UI 문구

## 2. 정본 여부 정의

### `canonical`

구현/판단 기준 문서다.  
문서 간 충돌이 발생하면 `canonical` 문서를 우선한다.

### `reference`

이해를 돕는 참고 문서다.  
배경, 예시, 패널 설명, 원천 자료, 검증 사례를 제공할 수 있으나 `canonical` 문서를 덮어쓰지 못한다.

### `archive`

과거 기록 보존용 문서다.  
현재 기준 문서가 아니며, 의사결정 근거 추적이나 히스토리 확인용으로만 사용한다.

## 3. 충돌 시 우선순위

문서 간 충돌이 발생하면 아래 순서로 우선한다.

1. 이 문서 `[00_CANONICAL_INDEX_KR.md]`
2. [spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md)
3. 현재 구현 기준 재구축 v2 문서
4. 기존 `canonical` 문서
5. `reference` 문서
6. `archive` 문서

추가 원칙:
- `phase`, `review`, `handoff`, `experiment` 문서는 단독으로 구현 기준이 될 수 없다.
- 예시 문서(`request-response-examples.md` 등)는 설명용이며, 계약 충돌 시 기술명세 본문이 우선한다.

## 4. 현재 문제 정의

참고 문서의 실제 위치와 하위 분류는 [reference/00_REFERENCE_INDEX_KR.md](./reference/00_REFERENCE_INDEX_KR.md)에서 관리한다.

현재 `docs/`에서 가장 큰 문제는 문서 수가 아니라, 여러 문서가 동시에 정본처럼 보인다는 점이다.

대표 문제:
- `README.md`, `APP_REBUILD_SPEC_KR.md`, `PHASE_STATUS_AND_UPGRADE_PLAN_KR.md`가 서로 다른 방식으로 기준 문서를 가리킨다.
- `api-spec.md`, `db-schema.md`, `job-lifecycle.md`, `TECHNICAL_SPEC_GUI_PARITY_KR.md`가 기술 계약의 일부를 각각 따로 들고 있다.
- `PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md`는 기능/기술/권한/운영 규칙이 한 문서에 섞여 있다.
- `auth/org` 관련 용어와 역할 모델이 문서별로 드리프트할 위험이 있다.

따라서 지금 단계의 핵심은 문서 재작성보다 먼저 `정본 체계 선언`을 하는 것이다.

## 5. 우선 고정 용어

기술명세 통합 전이라도 아래 용어는 지금부터 표준으로 사용한다.

- `platform_admin`
  - 전역 운영자 역할
- `org_admin`
  - 회사/조직 관리자 역할
- `org_member`
  - 일반 회사 사용자 역할
- `organization`
  - 회사/고객사 단위
- `membership`
  - 사용자의 조직 소속 및 조직 내 역할
- `account_status`
  - 사용자 계정 자체의 상태
- `membership_status`
  - 특정 조직 소속 상태

설명 원칙:
- `platform_admin`은 조직 역할에 포함하지 않는다.
- `users.organization_id` 같은 단순 구조를 최종 모델로 사용하지 않는다.
- 조직 권한은 `membership` 기준으로 본다.

## 6. 목표 정본 문서 체계

최종적으로 살아남아야 하는 정본 문서는 6~7개다.

1. 기능명세서
2. 시스템 설계명세서
3. 기술명세서
4. 운영정책 명세서
5. UI 화면 명세서
6. 재구축 구현 플레이북
7. 선택적 원천 기준 문서

현재는 통합 전 과도기를 지나, `docs/spec/` 아래의 정식 canonical 세트를 기준으로 사용한다.

## 7. 현재 Canonical Set

### 7.0 현재 구현 기준 재구축 v2 세트

아래 문서는 `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238` 구현을 기준으로 새 회사 또는 외부 구현팀에 전달하기 위한 현재 우선 정본이다.

1. [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md)
2. [IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md](./spec/IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md)
3. [REBUILD_FUNCTIONAL_SPEC_KR.md](./spec/REBUILD_FUNCTIONAL_SPEC_KR.md)
4. [REBUILD_UI_UX_SPEC_KR.md](./spec/REBUILD_UI_UX_SPEC_KR.md)
5. [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./spec/REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md)
6. [REBUILD_OPERATIONS_SECURITY_SPEC_KR.md](./spec/REBUILD_OPERATIONS_SECURITY_SPEC_KR.md)
7. [REBUILD_RFP_FINAL_SPEC_KR.md](./spec/REBUILD_RFP_FINAL_SPEC_KR.md)

기존 2026-03-22 정본 세트는 위 문서에 흡수된 구버전 정본으로 본다. 배경과 세부 참고 자료로는 사용할 수 있지만, 현재 구현 기준 재구축 발주/검수에서는 v2 세트가 우선한다.

### 7.1 번호 체계

1. [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md)
2. [01_DOCUMENT_METADATA_REGISTRY_KR.md](./01_DOCUMENT_METADATA_REGISTRY_KR.md)
3. [FUNCTIONAL_SPEC_KR.md](./spec/FUNCTIONAL_SPEC_KR.md)
4. [SYSTEM_DESIGN_KR.md](./spec/SYSTEM_DESIGN_KR.md)
5. [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md)
6. [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md)
7. [UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md)
8. [REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](./spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md)

## 8. 문서 분류표

| 문서 | 현재 분류 | 비고 |
| --- | --- | --- |
| [FUNCTIONAL_SPEC_KR.md](./spec/FUNCTIONAL_SPEC_KR.md) | `canonical` | 기능명세 본문 |
| [SYSTEM_DESIGN_KR.md](./spec/SYSTEM_DESIGN_KR.md) | `canonical` | 시스템 설계명세 본문 |
| [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | `canonical` | 기술명세 본문 |
| [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md) | `canonical` | 운영정책 본문 |
| [UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) | `canonical` | UI 화면 명세 본문 |
| [REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](./spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md) | `canonical` | 재구축 구현 플레이북 |
| [reference/source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md](./reference/source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md) | `reference` | 기능명세 원천 문서 |
| [reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md](./reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md) | `reference` | 설계명세 원천 문서 |
| [reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md](./reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md) | `reference` | 기술명세 원천 문서 |
| [reference/contracts/api-spec.md](./reference/contracts/api-spec.md) | `reference` | API 계약 부속 문서 |
| [reference/contracts/db-schema.md](./reference/contracts/db-schema.md) | `reference` | DB 계약 부속 문서 |
| [reference/contracts/job-lifecycle.md](./reference/contracts/job-lifecycle.md) | `reference` | 상태/전이 계약 부속 문서 |
| [reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md](./reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md) | `reference` | 운영정책 원천 재료 |
| [reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](./reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md) | `reference` | 메일/SMTP 정책 부속 문서 |
| [reference/contracts/request-response-examples.md](./reference/contracts/request-response-examples.md) | `reference` | 요청/응답 예시 |
| [reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](./reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md) | `reference` | 운영 편의 기능 |
| [reference/operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt](./reference/operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt) | `reference` | 화면/패널 참고 |
| [reference/operations/PHASE1_EQUIVALENCE_TEST_CASES_KR.md](./reference/operations/PHASE1_EQUIVALENCE_TEST_CASES_KR.md) | `reference` | 검증 기준 |
| [reference/operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md](./reference/operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md) | `reference` | phase/완료판정/우선순위 문서 |
| [reference/source/APP_REBUILD_SPEC_KR.md](./reference/source/APP_REBUILD_SPEC_KR.md) | `reference` | 원천 기준 참고서 |
| [archive/00_ARCHIVE_INDEX_KR.md](./archive/00_ARCHIVE_INDEX_KR.md) | `archive` | archive 인덱스 |
| [archive/notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md](./archive/notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md) | `archive` | 산출물 후속 작업 메모 |
| [archive/notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md](./archive/notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md) | `archive` | 기술 보조 노트 |
| [archive/notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md](./archive/notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md) | `archive` | 정책 분리 참고 |
| [archive/handoff/CONTRACT_LOOKUP_HANDOFF_KR.md](./archive/handoff/CONTRACT_LOOKUP_HANDOFF_KR.md) | `archive` | handoff |
| [archive/review/FILTER_PERFORMANCE_REVIEW_HANDOFF_KR.md](./archive/review/FILTER_PERFORMANCE_REVIEW_HANDOFF_KR.md) | `archive` | review/handoff |
| [archive/review/LLM_REVIEW_HANDOFF_KR.md](./archive/review/LLM_REVIEW_HANDOFF_KR.md) | `archive` | review/handoff |
| [archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_PLAN_KR.md](./archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_PLAN_KR.md) | `archive` | experiment plan |
| [archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_RESULTS_20260314_KR.md](./archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_RESULTS_20260314_KR.md) | `archive` | experiment result |

## 9. 문서 개편 순서

문서 개편은 아래 순서를 바꾸지 않는다.

1. 이 인덱스 문서 생성
2. 문서별 `canonical / reference / archive` 메타 부착
3. 기존 reference 문서를 `02/03/04/05` 본문 기준으로 재연결
4. `04/05` 본문에 세부 계약/정책 흡수
5. 마지막에 `handoff / review / experiment` 문서를 archive 경로로 이동

이 순서를 바꾸면 안 되는 이유:
- 통합본을 먼저 만들면 기존 문서와 새 문서가 동시에 정본처럼 읽힐 수 있다.
- 인덱스를 먼저 만들면 그 순간부터 해석 권한이 한곳으로 모인다.

## 10. 다음 단계

다음 작업은 아래 순서로 진행한다.

1. 각 문서 상단에 메타 추가
   - 문서 역할
   - 정본 여부
   - 상위 기준 문서
   - 충돌 시 우선 문서
2. 기존 부속 문서 상단 메타 정리
3. `TECHNICAL_SPEC_KR.md`에 세부 계약 흡수
4. `OPERATIONS_POLICY_KR.md`에 세부 규칙 흡수
5. `UI_SCREEN_SPEC_KR.md`에 실제 화면/모달/패널 규칙 흡수
6. `REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md`를 기준으로 구현 순서/모듈 분해/화면-API-DB 매핑을 유지

## 11. 결론

현재 단계의 핵심은 문서 삭제나 대규모 재작성보다 `정본 체계 선언`이다.

이 문서가 선언하는 기준은 아래와 같다.

- 정본은 적고 명확해야 한다.
- 참고 문서는 정본을 설명할 수 있지만 덮어쓸 수 없다.
- 아카이브 문서는 보존 대상이지 구현 기준이 아니다.
- `auth/org` 용어와 역할 구조는 지금부터 표준을 유지한다.

