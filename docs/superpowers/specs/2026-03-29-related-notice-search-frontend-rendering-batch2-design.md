# Related Notice Search Frontend Rendering Batch 2 Design

## Goal

`frontend/app.js`에 남아 있는 큰 렌더링 블록 중에서 다음 두 영역을 현재 runtime 패턴으로 분리한다.

- 조직 관리자 패널 잔여 마크업
- 영업 종료 아카이브 렌더링

이번 배치의 목적은 `app.js`에서 긴 템플릿 문자열과 표시용 집계 로직을 줄이고, 상태/이벤트 wiring만 유지하는 것이다.

## Scope

포함:

- `renderOrganizationAdminPanel()` 내부의 초대 목록, 감사 로그, 사용자 요약, 사용자 카드 마크업 생성 로직
- `renderClosedSalesArchiveSection()` 내부의 연/월 그룹화 및 아카이브 카드 마크업 생성 로직
- 해당 runtime 단위 테스트 추가 또는 확장
- `frontend/app.js`를 thin orchestration layer로 정리

제외:

- 트래커 보드 본문/편집 셀 분리
- 트래커 엔트리 카드 렌더링 분리
- 상태 구조 변경, 이벤트 흐름 변경, DOM 구조 재설계

## Design

### 1. Organization Admin Runtime Extension

대상 파일: `frontend/org-admin-runtime.js`

새 runtime helper를 추가한다.

- `buildInvitationListMarkup(payload, helpers)`
- `buildOrganizationAuditLogMarkup(payload, helpers)`
- `buildOrganizationMemberSummaryMarkup(payload, helpers)`
- `buildOrganizationMemberListMarkup(payload, helpers)`

이 helper들은 순수 마크업 계산만 담당한다. `escapeHtml`, 포맷 함수, role/status option 생성기, 보호 계정 판별기 같은 collaborator는 `app.js`에서 주입한다.

`frontend/app.js`의 `renderOrganizationAdminPanel()`은 아래 역할만 유지한다.

- admin mode / loading / error 상태 판별
- runtime helper 호출
- 버튼 disabled/title 갱신
- copy / revoke / save / delete 이벤트 바인딩

즉 `innerHTML`에 들어가는 긴 템플릿과 멤버 상태 카운트 집계는 runtime으로 이동하고, DOM 읽기와 이벤트 연결은 `app.js`에 남긴다.

### 2. Sales View Runtime Extension

대상 파일: `frontend/sales-view-runtime.js`

기존 active summary runtime에 더해 closed archive 쪽 helper를 추가한다.

- `buildClosedSalesArchiveSectionMarkup(payload, helpers)`

이 helper는 다음 책임을 가진다.

- 연/월 bucket grouping
- year/month section markup 생성
- claim archive card markup 생성
- 빈 상태 메시지 생성

`app.js`는 계속 아래 collaborator를 주입한다.

- `escapeHtml`
- `getSalesYearMonthBucket`
- `formatContractAmountDisplay`
- `extractContractAmountTextFromSalesNote`
- `formatSalesDateLabel`
- `truncate`
- `formatSalesNoteTextForDisplay`
- `getLatestSalesNoteItem`
- `salesClaimStatusLabel`

`renderSalesSummaryPanel()`은 active summary용 markup 조합과 이벤트 wiring만 유지하고, closed archive HTML은 runtime이 돌려준 문자열을 그대로 합성한다.

## Testing

추가/확장 테스트:

- `frontend/tests/org-admin-runtime.test.js`
  - 초대 목록 hidden hint / revoke button 조건
  - 멤버 요약 집계 마크업
  - protected/self member card locking 표시
- `frontend/tests/sales-view-runtime.test.js`
  - closed archive 연/월 grouping
  - contract amount 표시 조건
  - 빈 상태 메시지

검증:

- `node --test frontend/tests/org-admin-runtime.test.js frontend/tests/sales-view-runtime.test.js`
- `node --check frontend/org-admin-runtime.js frontend/sales-view-runtime.js frontend/app.js`

## Risks And Guardrails

- 상태 판별 순서는 바꾸지 않는다. loading/error/empty/admin gating은 기존 `app.js` 순서를 유지한다.
- 이벤트 selector와 `data-*` attribute 이름은 유지한다.
- runtime은 DOM 접근 없이 문자열과 view-model 계산만 담당한다.
- `app.js`에 남는 fallback branch는 기존과 같은 문자열을 유지한다.

## Success Criteria

- `renderOrganizationAdminPanel()`과 `renderClosedSalesArchiveSection()`의 긴 마크업 블록이 runtime helper로 이동한다.
- `frontend/app.js`는 상태 판별과 이벤트 wiring 위주로 줄어든다.
- 기존 UI 동작과 selector contract가 유지된다.
- runtime unit tests와 syntax check가 통과한다.
