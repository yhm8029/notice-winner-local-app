# Main Modularization Bootstrap Design

**Goal**

`feature/related-notice-search` 브랜치에서 7차 프런트 모듈화 대상으로 `bootstrap` 경계를 정리한다. 목표는 `home bootstrap + sales overview cache/snapshot` 관련 데이터 shape/helper 책임을 [`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js) 쪽으로 더 명확히 밀어 넣고, [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 API 호출, 상태 전이, DOM 반영, 이벤트 흐름 중심으로 유지하는 것이다.

## Background

- 1차부터 6차까지 프런트 모듈화는 모두 `app.js` 안의 화면 렌더 책임을 runtime/helper로 바깥에 빼는 방향으로 진행됐다.
- 현재 [`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js)는 이미 `storage identity`, `sales overview payload normalize`, `home bootstrap cache payload`, `tracker snapshot reuse` 일부 helper를 갖고 있다.
- 반면 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)에는 아직 `applyHomeBootstrapPayload`, `hydrateHomeBootstrapCache`, `persistHomeBootstrapCache`, `syncHomeBootstrapSalesCache`, `shouldUseHomeBootstrapTrackerSnapshot` 같은 cache/snapshot wiring이 섞여 있다.
- 이 차수는 `auth session`과 다르게 UI보다는 `data shape + cache/snapshot helper` 경계를 먼저 굳히는 작업이다.
- 이전 논의 기준으로 이번 범위에서는 `auth.bootstrapEmail`이나 인증 부트스트랩 UX는 다루지 않는다.

## Scope

### In Scope

- `home bootstrap` payload normalize / merge / cache payload helper 정리
- `sales overview` cache payload helper 정리
- `tracker snapshot reuse` 판단 helper 정리
- `storage identity` helper 유지 및 호출 경계 명확화
- `app.js`의 bootstrap 관련 cache/apply/persist 경로를 runtime helper 사용 기준으로 정리
- bootstrap runtime 전용 node test 추가 또는 보강
- app-side bootstrap integration test 추가 또는 보강

### Out of Scope

- `state.auth.bootstrapEmail`
- `canUseBootstrapSignUp()`
- `isBootstrapEmail()`
- auth session 초기화/로그인 흐름
- backend `home-bootstrap` / `sales-claims` API
- organization admin / tracker board / related notice 도메인 로직

## Design Principles

- 기능 추가 없이 데이터 shape와 cache/snapshot 계산 책임만 분리한다.
- [`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js)는 pure helper/view-model 계층으로 유지한다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 API 호출, state mutation, DOM render, event 흐름만 유지한다.
- `auth bootstrap`과 `home bootstrap cache`는 이름이 비슷해도 다른 축으로 취급한다.
- 이후 `main`으로 가져갈 때 `helper 확장 -> app wiring 정리 -> integration test` 순서로 잘게 쪼갤 수 있어야 한다.

## Approaches Considered

1. `helper/data-shape 우선`
- `bootstrap-runtime.js`에 normalize/merge/cache helper를 먼저 정리하고, `app.js`는 그 helper를 쓰도록 연결한다.
- 장점: 회귀 위험이 낮고, `main`으로 가져갈 단위가 작다.
- 장점: 이후 wiring 분리 때 기준 계약이 명확해진다.
- 단점: `app.js` 축소 폭은 1차에서 아주 크지 않을 수 있다.
- 추천안이다.

2. `load/apply wiring 우선`
- `loadHomeBootstrap`, `hydrateHomeBootstrapCache`, `persistHomeBootstrapCache` 같은 app 흐름을 먼저 떼어낸다.
- 장점: `app.js` 줄 수는 빨리 준다.
- 단점: helper 계약이 흐린 상태에서 wiring을 먼저 건드리면 테스트가 불안정해진다.

3. `console-data runtime으로 흡수`
- bootstrap 관련 흐름을 아예 `console-data-runtime` 쪽으로 더 밀어 넣는다.
- 장점: 장기적으로는 더 깔끔할 수 있다.
- 단점: 이번 차수 범위를 넘어서고, 다른 세션의 관련 작업과 충돌 위험이 높다.

## Recommended Design

이번 7차는 `helper/data-shape 우선`으로 간다.

### Runtime Responsibilities

[`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js)에서 아래 책임을 명확히 가진다.

- `buildStorageIdentity(authUser)`
- `normalizeSalesOverviewPayload(payload)`
- `buildSalesOverviewCachePayload(payload)`
- `mergeSalesOverviewIntoHomeBootstrapPayload(existingPayload, salesPayload)`
- `normalizeTrackerFirstPagePayload(payload, fallbackPageSize)`
- `buildHomeBootstrapCachePayload(payload)`
- `mergeTrackerEntriesById(previousEntries, nextEntries)`
- `canUseHomeBootstrapTrackerSnapshot(input)`
- `hasCachedSalesOverviewData(snapshotState)`
- `hasCachedHomeBootstrapData(snapshotState)`
- `isMissingSalesOverviewEndpointError(error)`
- `isMissingHomeBootstrapEndpointError(error)`

필요하면 이 차수에서 아래 helper를 추가할 수 있다.

- `buildHomeBootstrapApplyView(...)`
  - `tracker_first_page` 적용에 필요한 normalized page payload 반환
- `buildHomeBootstrapCacheSyncPayload(...)`
  - sales overview 결과를 기존 home bootstrap cache payload에 안전하게 합칠 payload 반환

위 helper는 모두 plain object만 반환해야 하고, `state`, `dom`, `localStorage`, `api()`를 직접 만지면 안 된다.

### App Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)는 아래 책임만 유지한다.

- `/api/home-bootstrap`, `/api/sales-claims/overview` 호출
- 응답을 state에 반영
- cache read/write 호출
- render 함수 호출
- fallback/flash/error 흐름

즉 `app.js`는 bootstrap 계산을 직접 소유하지 않고, runtime helper 결과를 조립해서 state mutation에만 사용한다.

## Target Refactor Boundary

### Stay In `app.js`

- `loadHomeBootstrap(...)`
- `loadHomeBootstrapFromLegacy(...)`
- `loadSalesOverview(...)`
- 실제 `state.*` 필드 mutation
- `renderTrackerEntries()`, `renderSalesSummaryPanel()` 등 화면 갱신 호출
- cache envelope read/write 호출 자체

### Move/Clarify Through Runtime

- payload normalize 규칙
- `tracker_first_page` fallback 규칙
- sales overview cache payload shape
- home bootstrap cache payload shape
- snapshot reuse predicate
- cached-data existence predicate
- previous tracker entries와 next tracker entries merge 규칙

## File Plan

### Modify

- [`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js)
  - helper 계약 명확화
  - 필요시 small pure helper 추가

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - bootstrap cache/apply/persist 경로가 runtime helper 기준으로 동작하도록 정리
  - inline normalize/fallback 계산 최소화

### Create / Expand Tests

- `tests/frontend/test_bootstrap_runtime.mjs`
  - payload normalize/merge/cache helper 검증
  - snapshot predicate 검증
  - missing-endpoint 판단 helper 검증

- `tests/frontend/test_bootstrap_app_integration.mjs`
  - `applyHomeBootstrapPayload()`가 runtime helper 결과를 통해 state를 반영하는지 검증
  - `persistSalesOverviewCache()` / `syncHomeBootstrapSalesCache()` 경로가 cache payload contract를 지키는지 검증

## Merge Strategy To Main

`main`으로는 아래 순서로 잘라서 가져간다.

1. `bootstrap-runtime.js` helper 확장 + runtime test
2. `app.js` bootstrap cache/snapshot wiring 정리
3. bootstrap app integration test 추가

이 순서를 지키면 `main`에서 bootstrap helper 계약만 먼저 검토한 뒤, app wiring을 별도 머지로 가져갈 수 있다.

## Risks

- `tracker_first_page` normalize 규칙이 바뀌면 첫 페이지 pagination/state가 어긋날 수 있다.
- sales overview payload shape를 잘못 합치면 cache에 stale field가 남거나 누락될 수 있다.
- snapshot reuse predicate가 틀리면 최신 데이터를 안 불러오거나 불필요한 API 호출이 늘 수 있다.
- 다른 세션의 `related notice read path` 변경과 같은 `app.js` dirty 영역을 건드리면 충돌 위험이 있다.

## Success Criteria

- bootstrap 관련 data-shape/helper 규칙이 [`frontend/bootstrap-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/bootstrap-runtime.js)에서 읽히도록 정리된다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)의 bootstrap cache/snapshot 경로에서 inline normalize/fallback 로직이 줄어든다.
- `home bootstrap + sales overview cache/snapshot` 계약이 테스트로 고정된다.
- `auth.bootstrapEmail`과 인증 부트스트랩 UX는 이번 차수에 섞이지 않는다.
