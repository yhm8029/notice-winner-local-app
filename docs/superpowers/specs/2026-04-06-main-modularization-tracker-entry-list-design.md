# Main Modularization Tracker Entry List Design

**Goal**

`feature/related-notice-search` 브랜치에서 `tracker entry list/detail 카드 렌더`를 3차 프런트 모듈화 대상으로 정리한다. 목표는 기능 변경 없이 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 의 entry list 표시 책임을 [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 로 이동시키고, 이후 `main`으로 작은 단위로 가져갈 수 있는 경계를 만드는 것이다.

## Background

- 1차 모듈화에서 `run view`, `tracker diagnostics` 를 runtime 경계로 분리했다.
- 2차 모듈화에서 `selected entry drawer` 의 표시 계산을 runtime helper 기반으로 옮겼다.
- 현재 `tracker entry list/detail 카드 렌더` 는 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js#L8022) 에 크게 남아 있고, 선택 상태, 카드 마크업, empty state, metrics 조합이 한 덩어리다.
- [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 는 아직 summary/detail 데이터 보정 helper 중심이고, 카드 렌더 helper 는 없다.
- 같은 파일 안의 `tracker board` 렌더는 인라인 수정까지 포함하므로 이번 범위에서 제외하는 것이 안전하다.

## Scope

### In Scope

- tracker entry list empty state copy 계산
- entry card 기본 view-model 계산
- entry card markup 생성
- display number, selected class, override meta 계산
- building automation estimate 표시 조합
- `trackerEntriesList` 렌더 경계 분리
- runtime 전용 node test 추가

### Out of Scope

- `renderTrackerBoard*`
- board inline edit / sort / form submit
- selected-entry drawer
- sales claim 로직 자체
- related notice 로직 자체
- tracker entry 상세 API 호출 흐름
- tracker entry 선택 이후 상태 전이 로직 전체

## Design Principles

- 기능 변경 없이 표시 계산과 카드 마크업 책임만 분리한다.
- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 상태 결정, API 호출, 이벤트 바인딩, sales/related notice 액션 실행을 계속 담당한다.
- [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 는 순수 helper 만 제공한다.
- sales claim / related notice 는 runtime 에서 직접 렌더하지 않고, `app.js` 가 주입할 slot markup 으로 처리한다.
- 이번 차수는 list/detail 카드 렌더까지만 다루고, `tracker board` 는 다음 차수로 미룬다.

## Recommended Approach

세 가지 접근 중 `view-model + markup` 분리를 채택한다.

1. `markup-only` 분리
- 가장 안전하지만 `app.js` 축소 효과가 작다.

2. `view-model + markup` 분리
- runtime 이 카드 표시값과 markup 을 계산하고, `app.js` 는 상태/이벤트만 담당한다.
- 이번 차수에서 가장 균형이 좋다.

3. `entry list controller` 분리
- 렌더와 이벤트 바인딩까지 통째로 이동하는 방식이다.
- sales claim / related notice / selected entry preload 까지 한 번에 묶여 범위가 너무 크다.

## Target Boundary

### Runtime Responsibilities

[`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) 에 아래 책임을 모은다.

- `buildTrackerEntriesEmptyStateView(options)`
- `buildTrackerEntryCardView(entry, options)`
- `buildTrackerEntryCardMarkup(entry, options)`
- `buildTrackerEntriesListMarkup(entries, options)`

runtime helper 는 문자열, 숫자, boolean, HTML markup 만 반환한다. DOM 조회, 이벤트 연결, 상태 갱신은 하지 않는다.

### App Responsibilities

[`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 는 아래 책임을 유지한다.

- `displayEntries` 계산
- `state.selectedEntryId`, `state.trackerRelatedEntryId` 갱신
- selected entry preload / refresh
- related notice / notice viewer / sales claim 버튼 바인딩
- textarea input, transfer, close, release 같은 action bind
- `renderTrackerBoard()` 호출과 board 연계

## Slot Strategy

카드 내부에서 변동성이 큰 영역은 runtime 이 직접 조립하지 않는다.

- sales claim section: `app.js` 가 미리 만든 HTML 문자열을 `salesSectionHtml` slot 으로 넣는다.
- related notice section: `app.js` 가 미리 만든 HTML 문자열을 `relatedNoticeHtml` slot 으로 넣는다.

이 방식이면 runtime 은 카드 외형과 공통 메타만 담당하고, 도메인 액션은 여전히 `app.js` 에 남는다.

## File Plan

### Modify

- [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js)
  - entry list/card helper 추가

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - `renderTrackerEntries` 의 inline markup 계산 제거
  - runtime helper 호출로 교체

### Create

- [`tests/frontend/test_tracker_entry_runtime.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_tracker_entry_runtime.mjs)
  - empty state, entry card, slot 주입, 선택 상태 테스트

## Merge Strategy To Main

`main` 으로는 바로 머지하지 않고 작은 단위로 나눈다.

1. `tracker-entry-runtime.js` helper 확장
2. `app.js` entry list 렌더 치환
3. runtime test 추가

이 순서를 유지하면 `tracker board` 와 충돌하지 않고 리뷰 범위를 좁게 유지할 수 있다.

## Risks

- sales claim / related notice 로직까지 runtime 으로 옮기면 범위가 급격히 커진다.
- `displayEntries` 계산과 selected state 정규화가 runtime 쪽으로 새어나가면 상태 경계가 흐려진다.
- `trackerEntriesList` click binding 대상 selector 가 카드 markup 변경으로 깨질 수 있다.
- board 와 list 가 같은 selected state 를 공유하므로 list 렌더만 바꿔도 selected row 연동이 깨질 수 있다.

## Success Criteria

- `renderTrackerEntries` 에서 카드 HTML 조합 코드가 줄어든다.
- entry list 표시 규칙을 [`frontend/tracker-entry-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-entry-runtime.js) helper 로 설명할 수 있다.
- sales claim / related notice 액션은 기존처럼 `app.js` 가 담당한다.
- `tracker board` 동작은 이번 차수에서 영향받지 않는다.
- node 기반 runtime 테스트로 entry card 표시 규칙을 빠르게 검증할 수 있다.
