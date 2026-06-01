# Main Modularization Selected Entry Drawer Design

**Goal**

`feature/related-notice-search` 브랜치에서 `selected entry drawer` 영역을 2차 프런트 모듈화 대상으로 정리한다. 목표는 기능 변경 없이 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 의 selected entry 표시 책임을 [`frontend/selected-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/selected-entry-runtime.js) 로 이동시키고, 나중에 `main`으로 작은 단위로 옮길 수 있는 구조를 만드는 것이다.

## Background

- 1차 모듈화에서 `run view` 와 `tracker diagnostics` 는 runtime 경계로 분리했다.
- 현재 `selected entry drawer` 는 runtime 파일이 이미 존재하지만, 실제 렌더 책임은 대부분 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 에 남아 있다.
- 특히 `renderSelectedEntry`, `renderSelectedEntryLoading`, `renderEntryFieldGrid`, `renderEntryDiagnostics`, `renderDrawer`, `syncPatchValueFromSelectedEntry` 가 하나의 표시 책임 덩어리로 묶여 있다.
- 이 영역은 `tracker entry list`, `tracker board`, `sales claim`, `related notice` 보다 경계가 더 선명해서 2차 모듈화 대상으로 적합하다.

## Scope

### In Scope

- selected entry 메타 표시 계산
- selected entry loading / empty copy 계산
- field grid markup 생성
- diagnostics markup 생성
- drawer field list / status line markup 생성
- patch panel 표시값 계산
- selected entry runtime 전용 node test 추가

### Out of Scope

- tracker entry list 렌더링
- tracker board 렌더링 및 인라인 수정
- sales claim 렌더링
- related notice 렌더링
- selected entry API 호출 흐름
- selected entry change events API 흐름
- drawer open/close 상태 전환 로직

## Design Principles

- 기능 변경 없이 표시 계산 책임만 분리한다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 상태 관리, API 호출, DOM 반영, 이벤트 바인딩을 계속 담당한다.
- [`frontend/selected-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/selected-entry-runtime.js) 는 순수 함수만 제공한다.
- runtime 은 `window`, `state`, `dom` 에 직접 접근하지 않는다.
- `main` 으로 가져갈 때는 기능 단위가 아니라 runtime 경계 단위로 머지할 수 있어야 한다.

## Recommended Approach

세 가지 접근 중 `view-model + markup` 분리를 채택한다.

1. `markup-only` 분리
- 가장 안전하지만 `app.js` 축소 효과가 작다.

2. `view-model + markup` 분리
- runtime 이 무엇을 보여줄지 계산하고 `app.js` 는 어디에 보여줄지만 담당한다.
- 현재 단계에서 가장 균형이 좋다.

3. `selected entry controller` 분리
- 렌더, 상태 동기화, 이벤트까지 한 번에 이동하는 방식이다.
- 첫 단계로는 범위가 너무 크다.

## Target Boundary

### Runtime Responsibilities

[`frontend/selected-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/selected-entry-runtime.js) 에 아래 책임을 모은다.

- `buildSelectedEntryMeta(entry, options)`
- `buildSelectedEntryLoadingView(entry, options)`
- `buildSelectedEntryEmptyView()`
- `buildEntryFieldGridMarkup(entry, options)`
- `buildEntryDiagnosticsMarkup(entry, options)`
- `buildDrawerView(entry, options)`
- `buildPatchPanelView(entry, options)`

위 helper 들은 문자열, boolean, HTML markup 만 반환한다. DOM 조회, 이벤트 연결, 포커스 이동은 하지 않는다.

### App Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 아래 책임을 유지한다.

- `state.selectedEntry` 와 관련 상태 갱신
- 상세 API 호출 및 캐시 사용
- `textContent` / `innerHTML` 반영
- field button / drawer button 클릭 바인딩
- patch input focus / select 처리
- audit log, change events, drawer open state 동기화

## File Plan

### Modify

- [`frontend/selected-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/selected-entry-runtime.js)
  - selected entry 표시 helper 추가
  - 기존 helper 들을 view-model 성격으로 정리

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - selected entry 표시 계산 중복 제거
  - runtime helper 호출로 교체

### Create

- [`tests/frontend/test_selected_entry_runtime.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_selected_entry_runtime.mjs)
  - loading / empty / patch panel / diagnostics / field grid 기준 테스트

## Merge Strategy To Main

`main` 으로는 바로 머지하지 않는다. 2차 모듈화가 끝난 뒤에도 작은 단위로 나눈다.

1. `selected-entry-runtime.js` helper 확장
2. `app.js` selected entry 표시 계산 치환
3. runtime test 추가

이 순서를 유지하면 `main` 에서도 리뷰 범위를 좁게 유지할 수 있다.

## Risks

- patch panel 표시 계산이 runtime 과 `app.js` 에 이중으로 남으면 분리 효과가 사라진다.
- diagnostics empty-state copy 가 바뀌면 동작 변경처럼 보일 수 있다.
- drawer field button binding 을 runtime 으로 옮기면 DOM 책임 경계가 다시 섞인다.
- selected entry loading 화면에서 summary-only / detailed 상태 차이를 놓치면 회귀가 생길 수 있다.

## Success Criteria

- `selected entry drawer` 표시 계산이 runtime helper 로 설명 가능해야 한다.
- `app.js` 에서 selected entry 표시용 문자열 조합 코드가 줄어들어야 한다.
- selected entry 동작은 기존과 동일해야 한다.
- node 기반 runtime 테스트로 selected entry 표시 규칙을 빠르게 검증할 수 있어야 한다.
- 이후 3차 모듈화에서 `tracker entry list/detail` 을 별도 범위로 이어갈 수 있어야 한다.
