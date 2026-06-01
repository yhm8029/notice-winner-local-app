# Main Modularization Organization Admin Design

**Goal**

`feature/related-notice-search` 브랜치에서 `organization admin` 화면을 5차 프런트 모듈화 대상으로 정리한다. 목표는 기능 변경 없이 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에 남아 있는 운영 UI 렌더 책임 중 `플랜 요약`, `초대`, `멤버 관리`를 [`frontend/organization-admin-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/organization-admin-runtime.js) 쪽으로 더 명확히 이동시키는 것이다.

## Background

- 1차 모듈화에서 `run view`, `tracker diagnostics`를 runtime 경계로 분리했다.
- 2차 모듈화에서 `selected entry drawer` 표시 계산을 runtime helper로 옮겼다.
- 3차 모듈화에서 `tracker entry list/detail 카드 렌더`를 runtime helper 기반으로 정리했다.
- 4차 모듈화에서 `tracker board` 렌더와 edit markup/view-model을 runtime helper 경계로 이동했다.
- 현재 [`frontend/organization-admin-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/organization-admin-runtime.js)는 패널 생성, 상태 메시지, 일부 마크업 생성, 액션 바인딩을 담당하고 있지만, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에는 여전히 organization admin 관련 상태 조합과 감사 로그를 포함한 전체 렌더 진입점이 남아 있다.
- 이번 차수에서는 `플랜 요약 + 초대 + 멤버 관리`를 먼저 고정하고, `감사 로그`는 다음 차수로 분리한다.

## Scope

### In Scope

- organization admin 플랜 요약 표시 계산
- organization invitation 목록 empty/loading/error/loaded state 계산
- organization member summary 계산
- organization member list 정렬 및 markup 계산
- invitation submit 버튼 disabled/title 계산
- organization admin runtime 전용 node test 추가

### Out of Scope

- organization audit log 렌더
- invitation create/revoke API 호출
- member save/delete API 호출
- organization admin panel mount 위치
- auth/bootstrap 초기화 흐름
- related notice UI

## Design Principles

- 기능 변경 없이 표시 계산 책임만 더 분리한다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 상태 조회, API 호출, DOM 반영, 이벤트 바인딩을 유지한다.
- [`frontend/organization-admin-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/organization-admin-runtime.js)는 순수 helper와 markup 생성에 집중한다.
- `감사 로그`는 일부러 이번 범위에서 제외해 5차 모듈화 범위를 작게 유지한다.
- 이후 `main`으로 옮길 수 있도록 runtime 확장과 `app.js` 치환을 분리 가능한 구조로 만든다.

## Recommended Approach

세 가지 접근 중 `플랜 요약 + 초대 + 멤버 관리` 단위의 `view-model + markup` 분리를 채택한다.

1. `organization admin 전체` 분리
- `app.js` 축소 효과는 크지만 범위가 너무 크다.
- 감사 로그까지 포함되면 회귀 지점이 늘어난다.

2. `플랜 요약 + 초대 + 멤버 관리` 분리
- 같은 운영 UI 묶음이라 경계가 자연스럽다.
- `감사 로그`를 제외해서 리뷰 범위가 적당하다.
- 지금 단계에 가장 균형이 좋다.

3. `초대`만 단독 분리
- 가장 안전하지만 `app.js` 축소 효과가 너무 작다.

## Target Boundary

### Runtime Responsibilities

[`frontend/organization-admin-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/organization-admin-runtime.js)에서 아래 책임을 명확히 가진다.

- `buildOrganizationPlanSummaryView(...)`
- `buildOrganizationInvitationListView(...)`
- `buildOrganizationMemberSummaryView(...)`
- `buildOrganizationMemberListView(...)`
- `buildOrganizationAdminMarkup(...)`

위 helper들은 문자열, boolean, markup만 반환한다. DOM 조회, API 호출, state 변경은 하지 않는다.

### App Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 아래 책임을 유지한다.

- `state`에서 organization admin 관련 값 읽기
- `getOrganizationPlanSummaryForDisplay()` 호출
- organization audit log 렌더
- invitation create/revoke, member save/delete 실행
- runtime 반환값을 DOM에 반영
- organization admin 액션 바인딩 호출

## File Plan

### Modify

- [`frontend/organization-admin-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/organization-admin-runtime.js)
  - 플랜 요약, 초대 목록, 멤버 summary/list helper 정리
  - `buildOrganizationAdminMarkup()` 내부 책임을 하위 helper로 분해

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - organization admin 표시 계산 중 runtime으로 옮길 부분 제거
  - 감사 로그는 계속 `app.js`에 남김

### Create

- [`tests/frontend/test_organization_admin_runtime.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_organization_admin_runtime.mjs)
  - 플랜 요약 view
  - invitation list loading/error/hidden pending state
  - member summary/list 정렬과 잠금 상태

## Merge Strategy To Main

`main`으로는 나중에 작은 단위로 가져간다.

1. `organization-admin-runtime.js` helper 분해와 테스트 추가
2. `app.js` organization admin 표시 계산을 runtime 경로로 치환
3. audit log는 별도 차수에서 정리

이 순서를 지키면 `main`에서 organization admin 모듈화만 따로 리뷰하기 쉽다.

## Risks

- 초대 목록과 멤버 목록의 한국어 copy가 바뀌면 기능 변경처럼 보일 수 있다.
- protected/self account 잠금 규칙이 runtime 이동 과정에서 깨지면 운영 위험이 생긴다.
- plan summary의 `upgrade_required` 처리와 submit 버튼 비활성 규칙이 달라지면 즉시 회귀가 난다.
- 감사 로그를 이번 차수에서 건드리면 범위가 다시 커진다.

## Success Criteria

- organization admin의 `플랜 요약`, `초대`, `멤버 관리` 표시 규칙이 runtime helper로 설명 가능해진다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에서 organization admin 관련 inline markup 계산이 줄어든다.
- invitation submit disabled/title, member lock/delete/save 표시가 기존과 동일하게 유지된다.
- 감사 로그는 동작을 건드리지 않고 그대로 남는다.
- node 기반 runtime 테스트로 organization admin 표시 규칙을 빠르게 검증할 수 있다.
