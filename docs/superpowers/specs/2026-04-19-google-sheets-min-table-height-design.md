# Google Sheets Minimum Table Height Design

## Goal

Google Sheets 기반 탭에서 헤더 드롭다운 필터를 적용해 행 수가 급격히 줄어들어도, 테이블 래퍼 높이가 초기 표시 높이보다 작아지지 않도록 유지한다. 이 규칙은 특정 시트만이 아니라 같은 Google Sheets 테이블 UI를 쓰는 모든 시트에 공통 적용한다.

## Problem

현재 `frontend/app.js`의 `renderAdminGoogleSheetTable()`는 필터 상태가 바뀔 때마다 `buildAdminGoogleSheetTableView()` 결과를 그대로 다시 렌더한다. 이때 `.admin-google-sheet-table-wrap`는 내용물 높이에 맞춰 다시 계산되므로, 예를 들어 최근점검현황에서 `사급`처럼 1행만 남는 필터를 누르면 래퍼 높이도 함께 줄어든다.

이 축소는 단순 시각 문제를 넘어서 헤더 드롭다운 사용성을 깨뜨린다.

- 한 번 줄어든 뒤에는 다른 헤더 버튼을 누르기 어려워진다.
- 팝업 기준 영역이 지나치게 작아져 조작이 불안정해진다.
- 사용자는 새로고침으로만 원래 높이를 되찾게 된다.

## Requirements

- 각 Google Sheets 시트는 "처음 정상적으로 그려졌을 때의 테이블 높이"를 최소 높이 기준으로 삼는다.
- 필터 적용, 정렬 변경, 팝업 열기/닫기로 재렌더되어도 그 최소 높이 아래로 내려가지 않는다.
- 시트별 기준 높이는 서로 독립적이어야 한다.
- 데이터가 다시 늘어나 실제 높이가 더 커지면, 최소 높이 기준도 그 큰 값으로 갱신할 수 있어야 한다.
- 데이터/권한/탭 상태가 초기화되어 테이블이 사라질 때는 잘못된 높이를 다른 시트에 흘리지 않아야 한다.

## Approach

`frontend/app.js`에서 시트 키별 최소 높이 상태를 관리하고, 렌더 직후 실제 DOM 높이를 측정해 저장한다. `frontend/admin-google-sheets-runtime.js`는 저장된 최소 높이를 wrapper inline style로 받을 수 있게 하고, `frontend/styles.css`는 해당 값을 표준 `min-height`로 적용한다.

핵심은 고정 픽셀 상수를 넣는 것이 아니라 "사용자가 처음 본 그 시트의 실제 높이"를 그대로 최소값으로 보존하는 것이다. 이렇게 하면 최근점검현황처럼 기본 행 수가 많은 시트는 충분한 높이를 유지하고, 행 수가 적은 다른 시트는 필요 이상으로 큰 빈 공간을 만들지 않는다.

## State Model

`frontend/app.js`

- `state.adminGoogleSheetMinHeightByKey`
  - key: `sheet-...`
  - value: 측정된 최소 높이(px 숫자)

보조 동작:

- 현재 시트 렌더 후 wrapper 높이를 읽어 저장
- 저장된 높이가 있으면 다음 렌더에 그대로 전달
- 더 큰 실제 높이가 관측되면 저장값 갱신
- 시트 키가 없는 상태에서는 측정/적용하지 않음

## Rendering Flow

1. `renderAdminGoogleSheetTable(sheetKey, sheetPayload)`가 호출된다.
2. 해당 시트의 저장된 최소 높이를 조회한다.
3. `buildAdminGoogleSheetTableView()`에 `minTableHeightPx` 같은 옵션으로 전달한다.
4. 렌더 후 `.admin-google-sheet-table-wrap`를 찾아 실제 높이를 측정한다.
5. 측정값이 기존 저장값보다 크면 `state.adminGoogleSheetMinHeightByKey[sheetKey]`를 갱신한다.
6. 다음 필터 재렌더부터는 이 값이 다시 wrapper의 `min-height`로 적용된다.

## Runtime Markup Contract

`frontend/admin-google-sheets-runtime.js`

- wrapper element는 계속 `.admin-google-sheet-table-wrap`를 유지한다.
- 최소 높이 값이 전달된 경우 inline style 또는 CSS custom property를 포함한다.
- 값이 없으면 기존 마크업과 동일하게 동작한다.

추천 표현:

- `style="--admin-google-sheet-min-table-height: 512px; min-height: var(--admin-google-sheet-min-table-height);"`

이 방식은 테스트에서 문자열 검증이 쉽고, CSS fallback도 단순하다.

## Edge Cases

- 필터 결과가 0행이어도 최소 높이는 유지한다.
- stale-first 캐시 렌더처럼 초기 캐시 화면이 먼저 뜨는 경우에도, 현재 표시된 실제 높이를 기준으로 저장한다.
- 다른 시트로 전환했다가 돌아와도 시트별 저장값은 유지된다.
- 숨김 상태로 DOM이 제거되거나 비워질 때는 0 높이를 저장하지 않는다.

## Testing

추가/수정 테스트는 아래를 포함한다.

- runtime: 최소 높이 옵션이 wrapper markup에 반영되는지
- app integration: 한 시트에서 저장된 최소 높이가 필터 재렌더 후에도 유지되는지
- app integration: 더 큰 높이가 관측되면 저장값이 갱신되는지
- app integration: 다른 시트와 최소 높이 상태가 섞이지 않는지

## Non-Goals

- 헤더 드롭다운 위치 계산 로직 자체를 다시 바꾸지 않는다.
- Google Sheets 외 다른 표 컴포넌트까지 동일 로직을 확장하지 않는다.
- 서버 payload에 높이 메타데이터를 추가하지 않는다.
