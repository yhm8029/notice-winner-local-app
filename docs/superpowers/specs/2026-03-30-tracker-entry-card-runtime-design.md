# Tracker Entry Card Runtime Design

## Goal

`frontend/app.js`의 `renderTrackerEntries()` 안에 남아 있는 트래커 엔트리 카드 마크업을 `frontend/tracker-entry-runtime.js`로 분리한다.

이번 배치의 목적은 엔트리 카드 shell, 번호 배지, 헤더 버튼, 기본 메트릭, override 표시를 runtime이 소유하게 만들고, `app.js`는 필터링, 선택 상태, related/sales/event wiring만 유지하는 것이다.

## Scope

포함:

- `renderTrackerEntries()` 내부 카드 HTML 조립 로직 분리
- `frontend/tracker-entry-runtime.js`에 카드 마크업 helper 추가
- tracker entry runtime 테스트 파일 추가
- `app.js`에서 해당 helper 호출로 교체

제외:

- `renderTrackerBoard()` 관련 로직
- 엔트리 클릭/related toggle/notice view/sales action 이벤트 바인딩 변경
- `renderSalesClaimSection()` 내부 마크업 변경
- `renderTrackerEntryRelatedNotices()` 내부 마크업 변경
- selected-entry drawer/detail 편집

## Design

### 1. Runtime Boundary

대상 파일: `frontend/tracker-entry-runtime.js`

새 helper를 추가한다.

- `buildTrackerEntryCardMarkup(payload, helpers)`

runtime helper는 순수 HTML 문자열만 반환한다. 아래처럼 `app.js`가 이미 계산한 값은 payload로 넣는다.

- `displayNo`
- `selected`
- `relatedButtonLabel`
- `overrideMetaHtml`
- `salesClaimSectionHtml`
- `relatedNoticesHtml`

runtime helper 내부에서는 기본 entry 필드, 번호 배지, head action button markup, metrics block, 공사비 기반 추정 금액 표시를 조립한다.

### 2. App Ownership

대상 파일: `frontend/app.js`

`app.js`는 계속 아래 책임을 가진다.

- displayEntries 필터링
- selected/related state 결정
- sales section HTML 생성
- related notice HTML 생성
- card list를 DOM에 주입
- click / related toggle / notice view / sales action 이벤트 바인딩

즉 카드의 내용은 runtime으로 이동하지만, 카드 간 상태와 상호작용은 그대로 `app.js`가 관리한다.

### 3. Fallback Contract

`TRACKER_ENTRY_RUNTIME`는 nullable이므로, `app.js`에는 local fallback builder를 유지한다. runtime이 누락되거나 구버전이어도 카드 렌더링이 비지 않게 해야 한다.

## Risks And Guardrails

- 기존 `data-entry-id`, `data-entry-related-toggle`, `data-entry-notice-view` selector는 절대 바꾸지 않는다.
- admin 모드에서만 override meta paragraph가 보이는 규칙을 유지한다.
- related notice section과 sales section은 runtime이 직접 계산하지 않고, `app.js`에서 받은 HTML을 그대로 삽입한다.
- runtime helper는 DOM/state 접근 없이 payload와 helpers만 사용한다.

## Testing

추가 테스트:

- `buildTrackerEntryCardMarkup()`이 번호 배지, project name, entry key, related/notice 버튼 selector를 렌더링하는지
- `buildTrackerEntryCardMarkup()`이 metrics block과 추정 금액 문구를 렌더링하는지
- `buildTrackerEntryCardMarkup()`이 `salesClaimSectionHtml`, `overrideMetaHtml`, `relatedNoticesHtml`을 그대로 삽입하는지
- `app.js` fallback seam 테스트:
  - `TRACKER_ENTRY_RUNTIME = null`이어도 카드 렌더링 helper가 non-empty markup을 반환하는지

검증:

- `node --test frontend/tests/tracker-entry-runtime.test.js`
- `node --check frontend/tracker-entry-runtime.js frontend/app.js`

## Success Criteria

- `renderTrackerEntries()`에서 긴 카드 템플릿 문자열이 제거된다.
- `frontend/tracker-entry-runtime.js`가 카드 마크업 helper를 export한다.
- `app.js`는 이벤트 wiring과 state orchestration만 유지한다.
- runtime 누락 시에도 app-side fallback으로 카드 렌더링이 유지된다.
- 테스트와 syntax check가 통과한다.
