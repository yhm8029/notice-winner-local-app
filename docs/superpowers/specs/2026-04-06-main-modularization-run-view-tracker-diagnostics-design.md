# Main Modularization Run View Tracker Diagnostics Design

**Goal**

`feature/related-notice-search` 브랜치의 기존 runtime 분리 패턴을 이용해서 `main`에 없는 프런트 모듈화를 먼저 정리한다. 1차 대상은 `run view`와 `tracker diagnostics`이며, 목표는 기능 추가 없이 `frontend/app.js` 의 책임을 줄이고 `main`으로 단계적으로 옮길 수 있는 작은 머지 단위를 만드는 것이다.

## Background

- 현재 `feature/related-notice-search`는 `main`보다 프런트 분리가 더 진행된 상태다.
- 특히 [`frontend/run-view-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/run-view-runtime.js) 와 [`frontend/tracker-diagnostics-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-diagnostics-runtime.js) 는 이미 분리된 진입점이 있다.
- 반면 `main`은 여전히 [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js) 중심 구조라서, 큰 기능 브랜치를 통째로 머지하기보다 동작 유지형 모듈화만 먼저 가져가는 편이 안전하다.
- `auth`, `organization admin`, `related notice`는 의존성이 크고 동작 변화 위험이 크므로 1차 범위에서 제외한다.

## Scope

### In Scope

- `run view` 관련 렌더링과 보조 포맷팅 경계 정리
- `tracker diagnostics` 관련 렌더링, 패널 생성, 필터링 보조 경계 정리
- [`frontend/index.html`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/index.html) 의 runtime 스크립트 로딩 순서 명확화
- `main`에 옮길 때 필요한 최소 smoke 테스트와 node 기반 runtime 테스트 정리

### Out of Scope

- 로그인, 초대, 사용자 관리, organization admin 기능 확장
- related notice 도메인 로직 확장
- 백엔드 API 의미 변경
- `run view`/`tracker diagnostics` 외 다른 대형 화면 분리
- 디자인 변경, UX 변경, 문구 변경

## Design Principles

- 기능 변경 없이 파일 책임만 이동한다.
- `app.js`는 상태 저장, orchestrator, runtime 호출 지점만 남긴다.
- runtime 파일은 순수 렌더링, DOM 생성, 표시용 계산에 집중한다.
- 이벤트 바인딩은 가능하면 `app.js`에서 호출하고, runtime은 이벤트 대상 마크업과 lookup helper만 제공한다.
- `main` 머지 단위는 작아야 하므로 한 번에 하나의 runtime 경계만 옮길 수 있게 커밋을 쪼갠다.

## Target Boundaries

### 1. Run View Boundary

`run view`는 다음 책임을 runtime으로 이동 가능한 후보로 본다.

- run 카드 목록 마크업 생성
- run 상태 badge/view model 계산
- 페이지네이션 라벨 텍스트 생성
- 선택된 run detail의 표시 조합

`app.js`에 남길 책임은 다음과 같다.

- 실제 API 호출
- selected run state 갱신
- polling, SSE, retry, URL sync
- runtime 함수 호출 시점 제어

### 2. Tracker Diagnostics Boundary

`tracker diagnostics`는 다음 책임을 runtime으로 이동 가능한 후보로 본다.

- diagnostics 패널 DOM 생성
- contact resolution summary/list 마크업 생성
- cleanup preview 카드 마크업 생성
- backfill conflict 필터링 같은 순수 보조 함수

`app.js`에 남길 책임은 다음과 같다.

- diagnostics scope 계산
- API 호출 및 loading/error state 관리
- apply/refresh 버튼의 실제 action 실행
- admin 모드 조건 처리

## File Plan

### Files to Keep as Orchestrators

- [`frontend/app.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/app.js)
  - 상태
  - API 호출
  - runtime 호출
  - 이벤트 bind entrypoint

### Files to Strengthen

- [`frontend/run-view-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/run-view-runtime.js)
  - run list/detail rendering helper 집중
- [`frontend/tracker-diagnostics-runtime.js`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/tracker-diagnostics-runtime.js)
  - diagnostics panel rendering helper 집중

### Files to Touch for Loading/Integration

- [`frontend/index.html`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/index.html)
- [`frontend/vercel.json`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/frontend/vercel.json)
- [`tests/frontend/test_tracker_diagnostics_runtime.mjs`](C:/Users/HYUNMO/notice-winner-pipeline-web-remote/tests/frontend/test_tracker_diagnostics_runtime.mjs)
- 필요 시 `run view` runtime test 신규 추가

## Actual Main Merge Order

1. `run-view-runtime.js`
2. `tracker-diagnostics-runtime.js`
3. `frontend/index.html`, `frontend/vercel.json`, and this design doc as the final integration prep pass

## Merge Strategy To Main

### Phase A

`run view` 모듈화만 별도 커밋으로 정리한다.

- 기대 효과: `app.js`의 run 관련 렌더 비중 감소
- main 머지 단위: 프런트 rendering-only refactor

### Phase B

`tracker diagnostics` 모듈화만 별도 커밋으로 정리한다.

- 기대 효과: diagnostics 렌더/패널 생성 로직을 독립 파일로 유지
- main 머지 단위: diagnostics runtime refactor

### Phase C

`index.html` script order, `vercel.json` rewrite, runtime smoke test 정리를 별도 커밋으로 묶는다.

- 기대 효과: main으로 가져갈 때 로딩 문제 최소화
- main 머지 단위: integration-only change

## Risks

- `app.js`에서 상태와 DOM 참조가 runtime으로 과하게 새면, 분리는 했어도 경계가 불명확해진다.
- `run view`는 polling/SSE와 붙어 있어서 렌더 helper와 상태 갱신 로직을 섞으면 안 된다.
- `tracker diagnostics`는 admin-only 조건과 API scope 계산이 있으므로, scope 계산을 runtime으로 넘기면 경계가 흐려진다.
- `main`과 이 브랜치의 HTML/script 로딩 차이를 무시하면 runtime 파일만 옮기고 실제 로딩이 깨질 수 있다.

## Success Criteria

- `run view`와 `tracker diagnostics`가 각각 독립 runtime 경계로 문서화된다.
- `app.js`에서 해당 영역의 마크업 생성 책임이 줄어든다.
- 분리 결과가 기존 기능을 바꾸지 않는다.
- main에 가져갈 때 커밋을 기능별이 아니라 모듈 경계별로 나눌 수 있다.
- 최소 runtime 테스트와 node check로 분리 결과를 빠르게 검증할 수 있다.

## Recommendation

1차 모듈화는 `run view`부터 시작하고, 바로 뒤에 `tracker diagnostics`를 정리한다. 이 순서가 좋은 이유는 `run view`가 화면의 핵심이지만 비교적 순수 렌더 경계가 뚜렷하고, `tracker diagnostics`는 이미 runtime 분리 흔적이 있어 두 번째 슬라이스로 이어가기 쉽기 때문이다.
