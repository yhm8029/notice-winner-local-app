# 01 Document Metadata Registry

- 문서 역할: 문서 메타 레지스트리
- 정본 여부: `canonical`
- 이 문서가 답하는 질문: 각 문서의 역할, 정본 여부, 상위 기준, 충돌 시 우선 문서는 무엇인가
- 이 문서가 답하지 않는 질문: 개별 문서 본문 내용의 상세 요구사항
- 상위 기준 문서: [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md)

작성일: 2026-03-22  
목적: 기존 문서 상단 메타를 일괄 주입하기 전, 현재 문서 집합의 메타를 중앙에서 먼저 고정한다.

## 1. 왜 이 문서가 필요한가

기존 문서 일부는 인코딩/역사적 누적 때문에 직접 헤더를 일괄 수정하기보다, 먼저 중앙 레지스트리에서 해석 규칙을 고정하는 편이 안전하다.

이 문서는 각 문서의 메타를 중앙에서 선언하는 임시이자 공식적인 기준이다.

## 2. 메타 필드 정의

모든 문서는 아래 메타를 가진다고 본다.

- `문서 역할`
- `정본 여부`
- `이 문서가 답하는 질문`
- `상위 기준 문서`
- `충돌 시 우선 문서`

## 3. 문서 메타 표

참고 문서의 실제 위치와 하위 분류는 [reference/00_REFERENCE_INDEX_KR.md](./reference/00_REFERENCE_INDEX_KR.md)에서 함께 관리한다.

### 3.1 현재 구현 기준 재구축 v2 세트

아래 문서는 2026-04-30 기준 `origin/main` 실제 구현을 반영한 재구축 우선 정본이다. 기존 2026-03-22 정본 문서와 충돌하면 아래 v2 문서를 우선한다.

| 문서 | 문서 역할 | 정본 여부 | 상위 기준 문서 | 충돌 시 우선 문서 |
| --- | --- | --- | --- | --- |
| [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | 현재 구현 기준 문서 정리 매트릭스 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md](./spec/IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md) | 현재 구현 기준 갭 리포트 및 통합 마스터 | `canonical` | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) |
| [REBUILD_FUNCTIONAL_SPEC_KR.md](./spec/REBUILD_FUNCTIONAL_SPEC_KR.md) | 현재 구현 기준 재구축 기능명세서 | `canonical` | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) |
| [REBUILD_UI_UX_SPEC_KR.md](./spec/REBUILD_UI_UX_SPEC_KR.md) | 현재 구현 기준 재구축 UI/UX 명세서 | `canonical` | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) |
| [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./spec/REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md) | 현재 구현 기준 재구축 시스템/기술 명세서 | `canonical` | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) |
| [REBUILD_OPERATIONS_SECURITY_SPEC_KR.md](./spec/REBUILD_OPERATIONS_SECURITY_SPEC_KR.md) | 현재 구현 기준 재구축 운영/권한/보안 명세서 | `canonical` | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) |
| [REBUILD_RFP_FINAL_SPEC_KR.md](./spec/REBUILD_RFP_FINAL_SPEC_KR.md) | 외부 개발사/새 구현팀 전달용 최종 발주 명세서 | `canonical` | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) | [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./spec/DOCUMENT_GOVERNANCE_MATRIX_KR.md) |

### 3.2 기존 2026-03-22 정본 및 참고 문서

| 문서 | 문서 역할 | 정본 여부 | 상위 기준 문서 | 충돌 시 우선 문서 |
| --- | --- | --- | --- | --- |
| [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | 문서 체계 헌법 | `canonical` | 없음 | 자기 자신 |
| [01_DOCUMENT_METADATA_REGISTRY_KR.md](./01_DOCUMENT_METADATA_REGISTRY_KR.md) | 문서 메타 레지스트리 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [FUNCTIONAL_SPEC_KR.md](./spec/FUNCTIONAL_SPEC_KR.md) | 기능명세서 본문 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [SYSTEM_DESIGN_KR.md](./spec/SYSTEM_DESIGN_KR.md) | 시스템 설계명세서 본문 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | 기술명세서 본문 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md) | 운영정책 명세서 본문 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) | UI 화면 명세서 본문 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](./spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md) | 재구축 구현 플레이북 | `canonical` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [reference/source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md](./reference/source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md) | 기능명세 원천 문서 | `reference` | [FUNCTIONAL_SPEC_KR.md](./spec/FUNCTIONAL_SPEC_KR.md) | [FUNCTIONAL_SPEC_KR.md](./spec/FUNCTIONAL_SPEC_KR.md) |
| [reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md](./reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md) | 설계명세 원천 문서 | `reference` | [SYSTEM_DESIGN_KR.md](./spec/SYSTEM_DESIGN_KR.md) | [SYSTEM_DESIGN_KR.md](./spec/SYSTEM_DESIGN_KR.md) |
| [reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md](./reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md) | 기술명세 원천 문서 | `reference` | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) |
| [reference/contracts/api-spec.md](./reference/contracts/api-spec.md) | API 계약 부속 문서 | `reference` | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) |
| [reference/contracts/db-schema.md](./reference/contracts/db-schema.md) | DB 계약 부속 문서 | `reference` | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) |
| [reference/contracts/job-lifecycle.md](./reference/contracts/job-lifecycle.md) | 상태/전이 계약 부속 문서 | `reference` | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) |
| [reference/contracts/request-response-examples.md](./reference/contracts/request-response-examples.md) | 요청/응답 예시 부록 | `reference` | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) |
| [reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md](./reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md) | 운영정책/기술정책 원천 문서 | `reference` | [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md) | [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md) |
| [reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](./reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md) | 메일 발송 운영정책 부속 문서 | `reference` | [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md) | [OPERATIONS_POLICY_KR.md](./spec/OPERATIONS_POLICY_KR.md) |
| [reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](./reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md) | 운영 편의 기능 참고 | `reference` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [reference/operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt](./reference/operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt) | 화면/패널 참고 | `reference` | [06_UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) | [06_UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) |
| [archive/notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md](./archive/notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md) | 산출물 후속 작업 메모 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md](./archive/notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md) | 기술 보조 노트 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md](./reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md) | 재구축 검증용 골든 시나리오 | `reference` | [REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](./spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md) | [REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](./spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md) |
| [reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md](./reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md) | 화면-API-DB 필드 매핑 | `reference` | [UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) | [TECHNICAL_SPEC_KR.md](./spec/TECHNICAL_SPEC_KR.md) |
| [reference/rebuild/UI_STATE_MATRIX_KR.md](./reference/rebuild/UI_STATE_MATRIX_KR.md) | UI 상태 매트릭스 | `reference` | [UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) | [UI_SCREEN_SPEC_KR.md](./spec/UI_SCREEN_SPEC_KR.md) |
| [reference/operations/PHASE1_EQUIVALENCE_TEST_CASES_KR.md](./reference/operations/PHASE1_EQUIVALENCE_TEST_CASES_KR.md) | 검증 기준 참고 | `reference` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [reference/operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md](./reference/operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md) | phase/완료판정/우선순위 참고 | `reference` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [reference/source/APP_REBUILD_SPEC_KR.md](./reference/source/APP_REBUILD_SPEC_KR.md) | 원천 기준 참고 문서 | `reference` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/00_ARCHIVE_INDEX_KR.md](./archive/00_ARCHIVE_INDEX_KR.md) | archive 인덱스 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md](./archive/notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md) | 정책 분리 참고 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/handoff/CONTRACT_LOOKUP_HANDOFF_KR.md](./archive/handoff/CONTRACT_LOOKUP_HANDOFF_KR.md) | handoff 문서 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/review/FILTER_PERFORMANCE_REVIEW_HANDOFF_KR.md](./archive/review/FILTER_PERFORMANCE_REVIEW_HANDOFF_KR.md) | review/handoff 문서 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/review/LLM_REVIEW_HANDOFF_KR.md](./archive/review/LLM_REVIEW_HANDOFF_KR.md) | review/handoff 문서 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_PLAN_KR.md](./archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_PLAN_KR.md) | 실험 계획 문서 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |
| [archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_RESULTS_20260314_KR.md](./archive/experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_RESULTS_20260314_KR.md) | 실험 결과 문서 | `archive` | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) | [00_CANONICAL_INDEX_KR.md](./00_CANONICAL_INDEX_KR.md) |

## 4. 운영 원칙

1. 기존 문서 상단 메타를 바로 일괄 수정하지 못하더라도, 현재 해석 기준은 본 레지스트리를 따른다.
2. 추후 각 문서 상단에 동일 메타를 직접 삽입하더라도, 이 레지스트리의 정의와 충돌하면 안 된다.
3. 문서 개편이 진행되면 이 레지스트리를 먼저 갱신하고, 개별 문서를 그다음 수정한다.

