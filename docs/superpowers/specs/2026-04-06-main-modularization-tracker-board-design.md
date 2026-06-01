# Main Modularization Tracker Board Design

**Goal**

`feature/related-notice-search` 브랜치에서 `tracker board` 렌더링을 4차 프런트 모듈화 대상으로 정리한다. 목표는 기능 변경 없이 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 의 board rendering 책임을 runtime helper로 이동시키고, `renderTrackerBoard*` 덩어리를 `main`에 나중에 작은 단위로 옮길 수 있는 구조로 만드는 것이다.

## Background

- 1차 모듈화에서 `run view`, `tracker diagnostics` 를 runtime 경계로 분리했다.
- 2차 모듈화에서 `selected entry drawer` 의 표시 계산을 runtime helper 기반으로 옮겼다.
- 3차 모듈화에서 `tracker entry list/detail 카드 렌더` 를 runtime helper 기반으로 옮겼다.
- 현재 남은 큰 프런트 덩어리 중 하나가 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js#L8237) 부근의 `tracker board` 렌더링이다.
- 이 영역은 table markup, blank-priority 정렬, cell state, edit form markup, key hint, empty state가 섞여 있다.
- 반면 저장 API 호출, `trackerBoardEdit` 상태 전이, save/cancel action, keydown/input 핸들링까지 한 번에 옮기면 범위가 너무 커진다.

## Scope

### In Scope

- board empty state markup
- board header markup
- board row/cell view-model 계산
- blank-priority 정렬 helper
- edit form markup
- board table markup
- board rendering 전용 runtime test 추가

### Out of Scope

- `saveTrackerBoardEdit`
- `beginTrackerBoardEdit`
- `resetTrackerBoardEdit`
- `trackerBoardEdit` 상태 전이
- submit/click/input/keydown 이벤트 바인딩 자체
- tracker entry list rendering
- selected-entry drawer

## Design Principles

- 기능 변경 없이 board 표시 계산과 markup 생성 책임만 분리한다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 selected state, edit state, event binding, save/cancel 흐름을 계속 담당한다.
- runtime 은 순수 helper 만 제공하고, DOM 조회나 이벤트 연결은 하지 않는다.
- 편집 기능은 `state.trackerBoardEdit` 를 그대로 쓰되, 그 상태를 표시용 view-model 로 바꾸는 곳만 runtime 으로 옮긴다.
- board 와 list 가 같은 selected state 를 공유하므로, board runtime 은 state 변경 없이 표시만 계산해야 한다.

## Recommended Approach

세 가지 접근 중 `view-model + markup` 분리를 채택한다.

1. `rendering-only`
- 빈 상태와 table markup 만 runtime 으로 옮긴다.
- 가장 안전하지만 cell/edit 분리가 덜 된다.

2. `view-model + markup`
- runtime 이 header, row, cell, edit-form, blank-priority 정렬을 담당한다.
- `app.js` 는 이벤트와 상태 전이만 담당한다.
- 지금 단계에서 가장 균형이 좋다.

3. `board controller`
- 렌더, 편집, 이벤트, 저장 흐름까지 runtime/controller 로 옮긴다.
- 현재 단계에서 범위가 너무 크다.

## Target Boundary

### Runtime Responsibilities

새 helper 를 [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 에 추가한다.

- `buildTrackerBoardEmptyStateView()`
- `buildSortedTrackerBoardEntries(entries, options)`
- `buildTrackerBoardHeaderCellMarkup(column, options)`
- `buildTrackerBoardCellMarkup(entry, column, options)`
- `buildTrackerBoardEditingCellMarkup(entry, options)`
- `buildTrackerBoardRowMarkup(entry, options)`
- `buildTrackerBoardMarkup(entries, options)`

이 helper 들은 문자열, 배열, boolean, HTML markup 만 반환한다. DOM 조회와 이벤트 연결은 하지 않는다.

### App Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 아래 책임을 유지한다.

- `state.trackerBoardSort`, `state.trackerBoardEdit` 갱신
- board row click 처리
- edit 시작 / cancel / submit / input / keydown 이벤트
- `saveTrackerBoardEdit()` 호출
- `renderTrackerEntries()` 와의 연계

## File Plan

### Modify

- [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js)
  - board rendering helper 추가

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - `renderTrackerBoard`, `renderTrackerBoardHeaderCell`, `getSortedTrackerBoardEntries`, `renderTrackerBoardCell`, `renderTrackerBoardEditingCell` 의 inline 계산 제거
  - runtime helper 호출로 교체

### Create

- [`tests/frontend/test_tracker_board_runtime.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_tracker_board_runtime.mjs)
  - empty state, sort, cell/edit markup 테스트

- [`tests/frontend/test_tracker_board_app_integration.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_tracker_board_app_integration.mjs)
  - `renderTrackerBoard()` 가 runtime helper 경로를 사용하는지 구조적으로 검증

## Merge Strategy To Main

`main` 으로는 바로 머지하지 않고 작은 단위로 나눈다.

1. board runtime helper 추가
2. `renderTrackerBoard*` runtime 치환
3. board runtime 테스트 추가

이 순서를 유지하면 기존 1~3차 모듈화와 같은 패턴으로 리뷰 범위를 좁게 유지할 수 있다.

## Risks

- `trackerBoardEdit` 상태 해석이 runtime 과 `app.js` 에 이중으로 남으면 경계가 흐려진다.
- 정렬 helper 를 runtime 으로 옮기면서 현재 blank-priority 규칙이 바뀌면 회귀가 생긴다.
- edit textarea/input markup 이 바뀌면 keyboard binding selector 가 깨질 수 있다.
- board empty state copy 가 바뀌면 사용자 체감 회귀처럼 보일 수 있다.

## Success Criteria

- `renderTrackerBoard*` 덩어리의 markup 계산 코드가 줄어든다.
- board empty state, 정렬, cell/edit markup 규칙을 runtime helper 로 설명할 수 있다.
- 저장 API와 이벤트 바인딩은 계속 `app.js` 가 담당한다.
- board 선택/수정 동작은 기존과 동일해야 한다.
- node 기반 runtime 테스트로 board 표시 규칙을 빠르게 검증할 수 있어야 한다.
