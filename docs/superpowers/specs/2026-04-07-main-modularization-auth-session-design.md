# Main Modularization Auth Session Design

**Goal**

`feature/related-notice-search` 브랜치에서 `auth session` 화면과 form state 계산을 6차 프런트 모듈화 대상으로 정리한다. 목표는 기능 변경 없이 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에 남아 있는 인증 UI 표시 계산을 [`frontend/auth-session-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/auth-session-runtime.js)로 더 이동시키고, `app.js`는 인증 API 호출, 상태 전이, 이벤트 실행 흐름 중심으로 남기는 것이다.

## Background

- 1차에서 `run view`, `tracker diagnostics`를 runtime 경계로 분리했다.
- 2차에서 `selected entry drawer` 표시 계산을 runtime helper로 옮겼다.
- 3차에서 `tracker entry list/detail 카드 렌더`를 runtime helper 기반으로 정리했다.
- 4차에서 `tracker board` 렌더와 edit markup/view-model을 runtime helper 경계로 이동했다.
- 5차에서 `organization admin`의 `플랜 요약`, `초대`, `멤버 관리` 표시 계산을 runtime helper로 정리했다.
- 현재 [`frontend/auth-session-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/auth-session-runtime.js)는 세션 normalize, invitation preview view-model, 기본 auth shell view-model 정도만 담당하고 있다.
- 반면 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에는 여전히 `renderAuthUi()`, `syncAuthFormWithInvitationPreview()`, auth mode 토글과 form 상태 반영 로직이 크게 남아 있다.
- `bootstrap-runtime.js`는 sales/tracker snapshot cache와 home bootstrap 데이터 조합을 담당하는 별도 축이라 이번 차수에서 제외한다.

## Scope

### In Scope

- auth shell 표시 계산
- invitation preview 표시 계산 보강
- auth form field lock / visibility / submit text / autocomplete 계산
- session action label 계산
- auth session runtime 전용 node test 추가
- app-side auth UI 렌더 경로 integration test 추가

### Out of Scope

- `initializeAuthGate()`
- `loadInvitationPreview()`, `loadInvitationPreviewByEmail()`
- `importAuthSessionFromLocationHash()`
- `acceptPendingInvitationToken()`
- `handleAuthSubmit()`, `handleAuthPasswordReset()`, `handleAuthSignOut()`
- `bootstrap-runtime.js`
- backend auth API

## Design Principles

- 기능 변경 없이 표시 계산 책임만 더 분리한다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 인증 API 호출, state 전이, DOM 이벤트, flash/error 처리 중심으로 남긴다.
- [`frontend/auth-session-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/auth-session-runtime.js)는 순수 helper와 view-model 계산에 집중한다.
- 인증 초기화와 invitation acceptance 같은 네트워크 흐름은 이번 차수에서 건드리지 않는다.
- 이후 7차 `bootstrap` 모듈화로 자연스럽게 이어질 수 있도록, `auth session`과 `bootstrap cache` 경계를 섞지 않는다.

## Recommended Approach

세 가지 접근 중 `UI/view-model 우선 분리`를 채택한다.

1. `UI/view-model 우선 분리`
- `renderAuthUi()`, invitation preview, form field 상태를 runtime helper로 밀어 넣는다.
- `app.js`는 네트워크와 이벤트만 유지한다.
- 지금 단계에 가장 안전하고, 이전 1~5차 모듈화 패턴과도 일관된다.

2. `초기화 흐름까지 한 번에 분리`
- `initializeAuthGate()`, invitation preview 로딩, hash import, pending invite accept까지 같이 뺀다.
- 축소 폭은 크지만 인증 플로우 회귀 위험이 너무 크다.

3. `이벤트만 먼저 분리`
- submit/reset/signout/mode toggle만 따로 뺀다.
- 구조 개선 효과가 작고, 표시 계산 복잡도는 그대로 남는다.

## Target Boundary

### Runtime Responsibilities

[`frontend/auth-session-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/auth-session-runtime.js)에서 아래 책임을 더 명확히 가진다.

- `buildAuthUiViewModel(...)`
- `buildAuthInvitationPreviewViewModel(...)`
- `buildAuthFormFieldViewModel(...)`
- `buildAuthSessionActionViewModel(...)`
- 필요하면 위 helper를 조합하는 `buildAuthRenderState(...)`

위 helper들은 문자열, boolean, plain object만 반환한다. DOM 조회, API 호출, state 변경은 하지 않는다.

### App Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 아래 책임을 유지한다.

- auth 관련 API 호출
- invitation preview fetch와 debounce
- hash import / pending invite accept
- submit/reset/signout 실행
- runtime 결과를 DOM에 반영
- auth 관련 이벤트 바인딩

## File Plan

### Modify

- [`frontend/auth-session-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/auth-session-runtime.js)
  - auth form field / session action helper 추가
  - auth shell view-model 책임 정리

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - `renderAuthUi()`와 `syncAuthFormWithInvitationPreview()`의 표시 계산 중 runtime으로 옮길 부분 제거
  - auth 네트워크 흐름은 그대로 유지

### Create

- [`tests/frontend/test_auth_session_runtime.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_auth_session_runtime.mjs)
  - auth shell view-model
  - auth invitation preview
  - form field lock / submit text / autocomplete

- [`tests/frontend/test_auth_session_app_integration.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_auth_session_app_integration.mjs)
  - `renderAuthUi()`가 runtime helper 결과를 반영하는지 behavioral integration 검증

## Merge Strategy To Main

`main`으로는 나중에 작은 단위로 가져간다.

1. `auth-session-runtime.js` helper 확장과 runtime test 추가
2. `app.js` auth UI 렌더를 runtime 경로로 치환
3. auth integration test 추가

이 순서를 지키면 `main`에서 auth session 표시 계층만 따로 리뷰하기 쉽다.

## Risks

- sign-in / sign-up 모드 전환 copy가 바뀌면 바로 사용자 체감 회귀가 난다.
- invitation preview의 email lock/display-name autofill 규칙이 달라지면 sign-up 흐름이 깨질 수 있다.
- auth shell / console shell hidden 토글이 달라지면 인증되지 않은 사용자가 빈 화면을 보거나 반대로 콘솔이 잘못 열릴 수 있다.
- `bootstrapEmail` 관련 sign-up 가드가 잘못 옮겨지면 초기 운영자 등록 UX가 깨질 수 있다.

## Success Criteria

- auth shell의 표시 규칙이 runtime helper로 설명 가능해진다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에서 auth UI 관련 inline 상태 계산이 줄어든다.
- sign-in / sign-up, invitation preview, bootstrap email 관련 표시 동작이 기존과 동일하게 유지된다.
- auth session integration test가 runtime-composition 경로를 behavioral하게 검증한다.
- 이후 7차 `bootstrap` 모듈화로 자연스럽게 이어질 수 있다.
