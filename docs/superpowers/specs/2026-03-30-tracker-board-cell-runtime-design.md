# Tracker Board Cell Runtime Design

## Goal

`frontend/app.js`의 트래커 보드 렌더링 중 셀 마크업과 편집 셀 마크업만 `frontend/tracker-board-runtime.js`로 분리한다.

이번 배치의 목적은 보드 셀 템플릿 문자열을 `app.js`에서 제거하면서도, 정렬 상태, 선택 상태, 편집 시작/저장/취소 이벤트 wiring은 그대로 `app.js`에 유지하는 것이다.

## Scope

포함:

- `renderTrackerBoardCell()`의 순수 셀 마크업 계산
- `renderTrackerBoardEditingCell()`의 순수 편집 셀 마크업 계산
- `tracker-board-runtime.js`에 대응 helper 추가
- `tracker-board-runtime.test.js`에 셀/편집 셀 테스트 추가
- `app.js`에서 해당 helper 호출로 교체

제외:

- `renderTrackerBoard()`의 테이블 shell 분리
- row click / sort / edit / submit / cancel / input 이벤트 바인딩 변경
- 트래커 엔트리 카드 렌더링 분리
- 상태 구조 변경

## Design

### 1. Runtime Boundary

대상 파일: `frontend/tracker-board-runtime.js`

새 helper를 추가한다.

- `buildTrackerBoardCellMarkup(payload, helpers)`
- `buildTrackerBoardEditingCellMarkup(payload, helpers)`

이 helper들은 DOM에 접근하지 않고 HTML 문자열만 반환한다. `escapeHtml`, `textarea field set`, `editable 여부`, `override 여부`, `saving/error state` 같은 값은 모두 caller가 payload/helpers로 넘긴다.

### 2. App Ownership

대상 파일: `frontend/app.js`

`app.js`는 계속 아래 책임을 가진다.

- 정렬된 엔트리 목록 계산
- 현재 편집 상태 판단
- 테이블 전체 조립
- row/select/edit/save/cancel/input 이벤트 바인딩
- `state.trackerBoardEdit` 갱신

즉 `renderTrackerBoard()`와 관련 이벤트 루프는 그대로 두고, 셀 한 칸에 대한 HTML 생성만 runtime으로 위임한다.

### 3. Data Contract

`buildTrackerBoardCellMarkup()` payload:

- `entry`
- `column`
- `displayNo`
- `value`
- `isEditing`
- `isOverridden`

`buildTrackerBoardEditingCellMarkup()` payload:

- `entryId`
- `fieldName`
- `label`
- `value`
- `saving`
- `errorMessage`
- `textarea`
- `rows`

helper는 기존 `data-*` contract를 유지해야 한다.

- `data-board-edit-trigger`
- `data-board-edit-entry-id`
- `data-board-edit-field`
- `data-board-edit-form`
- `data-board-edit-input`
- `data-board-edit-cancel`

## Risks And Guardrails

- 이벤트 selector 이름은 절대 바꾸지 않는다.
- textarea 여부와 `progress_note`의 row 수 규칙은 유지한다.
- non-editable cell은 기존과 같은 단순 `<td>` 출력 형식을 유지한다.
- override meta 문구와 edit hint 문구는 기존 문자열을 유지한다.
- runtime helper는 상태를 읽지 않고 전달받은 payload만 사용한다.

## Testing

추가 테스트:

- `buildTrackerBoardCellMarkup()`이 display number cell을 그대로 렌더링하는지
- `buildTrackerBoardCellMarkup()`이 override 상태의 editable cell에 `data-board-edit-*` selector와 meta 문구를 넣는지
- `buildTrackerBoardEditingCellMarkup()`이 textarea field에서 `rows="4"`와 error message를 렌더링하는지
- `buildTrackerBoardEditingCellMarkup()`이 text input field에서 `input`과 cancel/save 버튼 disabled 상태를 반영하는지

검증:

- `node --test frontend/tests/tracker-board-runtime.test.js`
- `node --check frontend/tracker-board-runtime.js frontend/app.js`

## Success Criteria

- `app.js`에서 셀/편집 셀 템플릿 문자열이 제거된다.
- `tracker-board-runtime.js`가 셀 마크업 helper를 export한다.
- 기존 `data-*` selector contract와 편집 UX가 유지된다.
- 관련 runtime 테스트와 syntax check가 통과한다.
