# 현재 구현 기준 문서 정리 매트릭스

- 문서 역할: 기존 명세서 정리표 및 현재 구현 기준 문서 체계 선언
- 정본 여부: `canonical`
- 기준 커밋: `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238`
- 작성일: 2026-04-30
- 상위 기준 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)
- 기준 마스터 문서: [IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md](./IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md)
- 목적: 새 구현팀이 기존 코드 없이도 현재 제품과 95% 이상 유사하게 재구축할 수 있도록, 어떤 문서를 살리고 어떤 문서를 흡수/참조/보류할지 고정한다.

## 1. 결론

현재 재구축 기준은 기존 2026-03-22 정본 세트가 아니라, 2026-04-29에 작성된 현재 구현 기준 마스터 문서와 본 문서가 선언하는 4개 재구축 명세서다.

현재 기준 문서 세트:

1. [REBUILD_FUNCTIONAL_SPEC_KR.md](./REBUILD_FUNCTIONAL_SPEC_KR.md)
2. [REBUILD_UI_UX_SPEC_KR.md](./REBUILD_UI_UX_SPEC_KR.md)
3. [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md)
4. [REBUILD_OPERATIONS_SECURITY_SPEC_KR.md](./REBUILD_OPERATIONS_SECURITY_SPEC_KR.md)
5. [REBUILD_RFP_FINAL_SPEC_KR.md](./REBUILD_RFP_FINAL_SPEC_KR.md)

위 5개 문서와 기존 문서가 충돌하면 위 5개 문서를 우선한다. 위 5개 문서끼리 충돌하면 [REBUILD_RFP_FINAL_SPEC_KR.md](./REBUILD_RFP_FINAL_SPEC_KR.md)는 발주/검수 관점의 상위 요약이고, 상세 구현 판단은 해당 영역별 4개 명세서를 우선한다.

## 2. 문서 처리 상태 정의

| 상태 | 의미 |
| --- | --- |
| `유지` | 현재 구현 기준과 충돌하지 않으며 계속 참고할 수 있다. |
| `우선 유지` | 현재 구현 기준 재구축 문서로 승격하여 새 정본처럼 사용한다. |
| `흡수` | 내용은 유효하지만 새 문서에 녹여 넣고 단독 정본으로는 쓰지 않는다. |
| `참조` | 배경/예시/검증 자료로만 사용한다. 충돌 시 새 명세가 이긴다. |
| `보류` | 현재 제품의 95% 재구축에는 필요하지 않다. 후속 사업화 범위다. |
| `아카이브` | 히스토리 확인용이다. 구현 기준으로 쓰지 않는다. |

## 3. 기존 정본 문서 처리표

| 문서 | 기존 역할 | 처리 | 이유 | 흡수/대체 대상 |
| --- | --- | --- | --- | --- |
| [IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md](./IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md) | 현재 구현 기준 갭 리포트 + 통합 초안 | `우선 유지` | `origin/main` 구현 기준을 가장 직접적으로 반영한다. | 본 문서와 4개 재구축 명세서의 상위 근거 |
| [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md) | 기존 기능명세서 | `흡수` | 큰 기능 흐름은 맞지만 Google Sheets 관리자, home bootstrap, download job, related notice snapshot, 최신 sales 이벤트가 빠져 있다. | [REBUILD_FUNCTIONAL_SPEC_KR.md](./REBUILD_FUNCTIONAL_SPEC_KR.md) |
| [UI_SCREEN_SPEC_KR.md](./UI_SCREEN_SPEC_KR.md) | 기존 UI 화면 명세서 | `흡수` | 기본 사용자/관리자 모드 설명은 유효하지만 관리자 탭, legacy route, Google Sheets 관리자, missing report, cleanup, download job 화면이 부족하다. | [REBUILD_UI_UX_SPEC_KR.md](./REBUILD_UI_UX_SPEC_KR.md) |
| [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md) | 기존 시스템 설계명세서 | `흡수` | 컴포넌트 경계는 유효하지만 local artifact file, memory job, current org scoped platform admin, child run reuse 기준을 보강해야 한다. | [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md) |
| [TECHNICAL_SPEC_KR.md](./TECHNICAL_SPEC_KR.md) | 기존 기술명세서 | `흡수` | API/DB 기준 일부가 실제 구현과 다르다. 특히 Auth/Sales endpoint, `tracker_entries.project_id`, sales event type, artifact storage 기준을 고정해야 한다. | [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md) |
| [OPERATIONS_POLICY_KR.md](./OPERATIONS_POLICY_KR.md) | 기존 운영정책 명세서 | `흡수` | 역할/초대/감사 원칙은 유효하지만 hard delete 호환, 초대 idempotency, 메일 fallback, org scope, 계정 상태 전이 기준을 현재 구현으로 맞춰야 한다. | [REBUILD_OPERATIONS_SECURITY_SPEC_KR.md](./REBUILD_OPERATIONS_SECURITY_SPEC_KR.md) |
| [REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](./REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md) | 기존 재구축 구현 순서 | `흡수` | 구현 순서 자료로 유효하지만 최종 외주/신규팀 발주 문서로는 범위/검수/납품물/클린룸 원칙이 부족하다. | [REBUILD_RFP_FINAL_SPEC_KR.md](./REBUILD_RFP_FINAL_SPEC_KR.md) |

## 4. reference 문서 처리표

| 문서 | 처리 | 이유 | 대상 |
| --- | --- | --- | --- |
| [reference/source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md](../reference/source/SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md) | `참조` | GUI 기능 원천 자료이나 현재 구현 이후 추가된 기능이 빠져 있다. | 기능/UI 참고 |
| [reference/source/APP_REBUILD_SPEC_KR.md](../reference/source/APP_REBUILD_SPEC_KR.md) | `참조` | 초기 재구축 원천 자료다. 현재 구현 기준과 충돌하면 새 문서를 우선한다. | 최종 발주본 참고 |
| [reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md](../reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md) | `참조` | 아키텍처 배경은 유효하나 현재 artifact/local job/runtime 정책을 보강해야 한다. | 시스템 기술 참고 |
| [reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md](../reference/source/TECHNICAL_SPEC_GUI_PARITY_KR.md) | `참조` | GUI parity 초기 기술 문서다. 최신 endpoint와 DB 기준은 새 문서를 우선한다. | 기술 참고 |
| [reference/contracts/api-spec.md](../reference/contracts/api-spec.md) | `흡수` | API 예시는 유효하지만 Auth/Sales endpoint 경로가 최신 구현과 다를 수 있다. | 시스템 기술 명세 |
| [reference/contracts/db-schema.md](../reference/contracts/db-schema.md) | `흡수` | DB 기준은 필요하지만 `tracker_entries.project_id` 같은 파생 필드 오해를 제거해야 한다. | 시스템 기술 명세 |
| [reference/contracts/job-lifecycle.md](../reference/contracts/job-lifecycle.md) | `흡수` | 상태 전이는 유효하지만 child run reuse와 자동 tracker export 기준을 반영해야 한다. | 시스템 기술 명세 |
| [reference/contracts/request-response-examples.md](../reference/contracts/request-response-examples.md) | `참조` | 예시는 설명 자료로 유지한다. 계약 충돌 시 기술 명세를 우선한다. | API 예시 |
| [reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md](../reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md) | `흡수` | 영업 정책 원천 문서이나 현재 구현 이벤트명/권한/이관 모델이 우선이다. | 기능/운영 명세 |
| [reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](../reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md) | `참조` | 메일 공급자 전략은 후속 운영 참고다. 현재 MVP는 link fallback 포함 초대 메일이다. | 운영 보안 명세 |
| [reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](../reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md) | `흡수` | 운영 편의 기능 일부가 현재 구현에 들어와 있다. | UI/운영 명세 |
| [reference/operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt](../reference/operations/WEB_CONSOLE_PANEL_GUIDE_KR.txt) | `흡수` | 패널 단위 설명은 UI 명세로 흡수한다. | UI/UX 명세 |
| [reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md](../reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md) | `유지` | 검수 시나리오의 골격으로 유효하다. 현재 구현 기준 시나리오를 추가해야 한다. | 최종 발주본 검수 |
| [reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md](../reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md) | `유지` | 화면/API/DB 추적에 유용하다. 최신 endpoint와 필드 기준을 보강해야 한다. | 시스템 기술/UI 참고 |
| [reference/rebuild/UI_STATE_MATRIX_KR.md](../reference/rebuild/UI_STATE_MATRIX_KR.md) | `유지` | UI 상태 검수 자료로 유효하다. Google Sheets/admin/download 상태를 추가해야 한다. | UI 검수 참고 |

## 5. top-level phase/handoff 문서 처리표

| 문서 | 처리 | 이유 |
| --- | --- | --- |
| [PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md](../PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md) | `흡수` | 인증/조직/초대 정책의 배경이다. 현재 구현 기준 운영 보안 명세에 반영한다. |
| [PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md](../PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md) | `흡수` | sales action 최소 모델의 원천이다. 최신 event type과 endpoint 기준으로 재정리한다. |
| [PHASE2_PLATFORM_LAYER_ARCHITECTURE_KR.md](../PHASE2_PLATFORM_LAYER_ARCHITECTURE_KR.md) | `참조` | 플랫폼 계층 배경이다. 현재 재구축 범위에는 상세보다 경계만 필요하다. |
| [PHASE2_DISCUSSION_AND_CURRENT_DESIGN_HANDOFF_KR.md](../PHASE2_DISCUSSION_AND_CURRENT_DESIGN_HANDOFF_KR.md) | `아카이브` | handoff 성격이다. 현재 구현 명세의 근거 추적용이다. |
| [PHASE3_BILLING_AND_PAYMENT_SPEC_KR.md](../PHASE3_BILLING_AND_PAYMENT_SPEC_KR.md) | `보류` | 현재 95% 재구축의 필수 범위가 아니다. 사업화 후속 범위다. |
| [CONTACT_SELECTION_RULES_V2_KR.md](../CONTACT_SELECTION_RULES_V2_KR.md) | `참조` | 연락처 선택 규칙 참고다. 현재 구현의 contact resolution summary와 충돌하면 새 명세를 우선한다. |
| [CONTACT_RESOLVER_V1_NEXT_STEPS_20260327_KR.md](../CONTACT_RESOLVER_V1_NEXT_STEPS_20260327_KR.md) | `참조` | 다음 단계 메모다. 구현 기준이 아니라 개선 후보로 둔다. |
| [PROJECT_GROUPING_QUALITY_KR.md](../PROJECT_GROUPING_QUALITY_KR.md) | `참조` | 프로젝트 그룹 품질 검수 자료다. |
| [PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md](../PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md) | `참조` | 릴리스 체크리스트다. |
| [TRACKER_QUALITY_BACKFILL_DESIGN_KR.md](../TRACKER_QUALITY_BACKFILL_DESIGN_KR.md) | `흡수` | missing/backfill/cleanup 기준을 현재 기능과 UI 명세에 반영한다. |
| [PROJECT_STATUS_CLEANUP_HANDOFF_20260320_KR.md](../PROJECT_STATUS_CLEANUP_HANDOFF_20260320_KR.md) | `아카이브` | handoff 성격이다. |
| [DEMAND_CONTACT_TARGET_TAXONOMY_GUIDE_V0_1_KR.md](../DEMAND_CONTACT_TARGET_TAXONOMY_GUIDE_V0_1_KR.md) | `참조` | 분류 체계 참고다. |
| [DEMAND_CONTACT_TARGET_TAXONOMY_GUIDE_V0_2_KR.md](../DEMAND_CONTACT_TARGET_TAXONOMY_GUIDE_V0_2_KR.md) | `참조` | 최신 분류 체계 참고다. |
| [ARCHITECT_OFFICE_LOFIN_HANDOFF_KR.md](../ARCHITECT_OFFICE_LOFIN_HANDOFF_KR.md) | `아카이브` | 특정 운영/인수인계 메모다. |

## 6. 새 정본 문서별 책임

| 새 문서 | 책임 | 흡수 대상 |
| --- | --- | --- |
| [REBUILD_FUNCTIONAL_SPEC_KR.md](./REBUILD_FUNCTIONAL_SPEC_KR.md) | 사용자가 무엇을 할 수 있어야 하는지, 업무 흐름과 기능 범위를 설명한다. | 기존 기능명세, sales 원천 문서, tracker/related notice 기능 요구 |
| [REBUILD_UI_UX_SPEC_KR.md](./REBUILD_UI_UX_SPEC_KR.md) | 어떤 화면과 패널이 존재하고 어떤 상태/버튼/빈 화면/오류가 보여야 하는지 설명한다. | 기존 UI 명세, panel guide, UI state matrix |
| [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md) | 아키텍처, API, DB, 실행 lifecycle, storage, job, 외부 연동 기술 계약을 설명한다. | 기존 시스템 설계, 기술명세, contracts |
| [REBUILD_OPERATIONS_SECURITY_SPEC_KR.md](./REBUILD_OPERATIONS_SECURITY_SPEC_KR.md) | 권한, 계정/초대, 감사, 삭제/비활성화, 메일, 배포/보안 운영 정책을 설명한다. | 기존 운영정책, auth/B2B, email, audit 문서 |
| [REBUILD_RFP_FINAL_SPEC_KR.md](./REBUILD_RFP_FINAL_SPEC_KR.md) | 외부 개발사 또는 새 회사에 전달할 발주/검수 기준을 설명한다. | 구현 플레이북, 골든 시나리오, 4개 정본 명세 요약 |

## 7. 사용 규칙

1. 새 개발팀에는 기존 코드가 아니라 본 문서, 4개 재구축 명세, 최종 발주본만 전달한다.
2. 기존 reference 문서는 설명 자료로만 사용하고 단독 구현 기준으로 전달하지 않는다.
3. 실제 회사 데이터, 계정 비밀, API key, 배포 secret, 기존 소스 코드는 전달하지 않는다.
4. 문서 간 충돌이 발생하면 `현재 구현 기준`이라고 표시된 문장을 우선한다.
5. `origin/main`의 현재 구현과 다르게 바꾸고 싶은 항목은 재구축 범위가 아니라 후속 개선 범위로 분리한다.

