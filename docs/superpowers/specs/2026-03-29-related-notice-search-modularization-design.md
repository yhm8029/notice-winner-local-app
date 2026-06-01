# Related Notice Search Modularization Design

**Date:** 2026-03-29

## Goal

`feature/related-notice-search` 브랜치의 현재 모듈화 방향을 유지하면서, 큰 파일에 남아 있는 응집된 로직을 낮은 회귀 위험으로 순차 분리한다.

이번 설계의 목적은 구조를 새로 설계하는 것이 아니라, 이미 자리 잡은 `backend/services/*_backend.py` 및 `frontend/*-runtime.js` 패턴을 일관되게 확장하는 것이다.

## Current State

현재 브랜치는 이미 점진 모듈화가 진행 중이다.

- 백엔드:
  - `backend/api/app.py`는 여전히 대형 진입점이지만, `report_job_backend.py`, `related_notice_collect_backend.py`, `auth_*_backend.py`처럼 단일 책임 서비스 모듈이 점차 늘고 있다.
  - `backend/api/auth_runtime.py`도 invitation, profile, session, organization 관련 보조 모듈로 일부가 분리되었다.
- 프론트엔드:
  - `frontend/app.js`는 여전히 크지만, `auth-session-runtime.js`, `related-notice-runtime.js`, `sales-view-runtime.js`, `tracker-entry-runtime.js` 등 화면/도메인별 runtime 파일이 이미 사용 중이다.
- 최근 커밋 흐름도 `지원 모듈 분리`, `seam 분리`, `runtime 분리`를 반복하고 있다.

이 상태는 대규모 재구성보다 `응집된 블록을 안전하게 분리하는 작업`에 적합하다.

## Design Principles

이번 모듈화는 아래 원칙만 따른다.

1. 기존 동작과 API 계약은 유지한다.
2. 분리 단위는 현재 파일 안에서 응집도가 높은 블록만 대상으로 한다.
3. 분리 후 호출부는 얇아져야 하며, 라우터/엔드포인트/전역 상태 구조는 불필요하게 바꾸지 않는다.
4. repository 레이어는 현 시점의 안정 seam으로 보고 유지한다.
5. 테스트가 이미 있는 블록부터 우선 분리해 회귀 위험을 줄인다.

## Approaches Considered

### 1. 보수적 점진 분리

대형 파일 내부의 응집된 로직 블록만 골라 별도 서비스/runtime 파일로 추출한다.

- 장점:
  - 현재 커밋 흐름과 가장 잘 맞는다.
  - 회귀 범위를 좁게 유지할 수 있다.
  - 각 작업이 짧고 검증 가능하다.
- 단점:
  - 완전한 구조 정리에 시간이 걸린다.

### 2. 영역별 대묶음 분리

백엔드나 프론트엔드 한 영역을 한 번에 크게 분해한다.

- 장점:
  - 눈에 보이는 구조 개선 속도가 빠르다.
- 단점:
  - 충돌과 회귀 위험이 커진다.
  - 리뷰와 검증 비용이 급격히 증가한다.

### 3. 구조 재설계 중심 개편

라우터, 패키지, 프론트 상태 구조까지 다시 설계한다.

- 장점:
  - 최종 형태는 더 깔끔할 수 있다.
- 단점:
  - 현재 브랜치 방향과 맞지 않는다.
  - 작업 범위가 커지고 실패 비용이 높다.

### Recommendation

`1. 보수적 점진 분리`를 채택한다.

## Scope

이번 모듈화의 구현 범위는 다음 순서로 잡는다.

### Backend First Wave

1. `tracker export workbook` 관련 블록 분리
   - 대상: `backend/api/app.py` 내 tracker export workbook 계산/캐시/응답 보조 로직
   - 목표 파일: `backend/services/tracker_export_workbook_backend.py`

2. `artifact preview` 관련 블록 분리
   - 대상: `backend/api/app.py` 내 artifact 파일을 preview payload로 바꾸는 응집된 로직
   - 목표 파일: `backend/services/artifact_preview_backend.py`

3. `sales claim` 지원 로직 분리
   - 대상: `backend/api/app.py` 내 sales claim 변환/요약/보조 로직
   - 목표 파일:
     - 우선 후보: `backend/services/sales_claim_backend.py`
     - 범위가 크면: `backend/services/sales_claim_export_backend.py`처럼 더 작게 분리

4. `auth session cookie` 관련 블록 분리
   - 대상: `backend/api/auth_runtime.py` 내 cookie payload encode/decode 및 session cookie write/read 보조 로직
   - 목표 파일: `backend/services/auth_session_cookie_backend.py`
   - 단, 위 세 작업 뒤에 진행한다.

### Frontend First Wave

1. tracker list / board 렌더링 분리
   - 대상: `frontend/app.js` 내 tracker list, board markup, row/view rendering 보조 함수
   - 목표 파일:
     - 기존 `frontend/tracker-entry-runtime.js` 확장 또는
     - 신규 `frontend/tracker-board-runtime.js`

2. organization admin panel 렌더링 분리
   - 대상: `frontend/app.js` 내 organization users/invitations/audit/admin panel template 및 view-model 정리
   - 목표 파일:
     - 신규 `frontend/org-admin-runtime.js` 우선
     - 또는 기존 `frontend/auth-session-runtime.js` 확장

3. sales summary / archive 렌더링 분리
   - 대상: `frontend/app.js` 내 sales summary, archive, audit-card 주변 markup helper
   - 목표 파일: `frontend/sales-view-runtime.js` 확장

## Explicit Non-Goals

아래 항목은 이번 모듈화에서 다루지 않는다.

1. repository 레이어 추가 분해
2. `auth account deletion / cleanup` 같은 고결합 정리 로직 분해
3. `frontend/app.js`의 전역 state, timer, API orchestration 전체 재설계
4. 라우터 패키지 구조 개편
5. 새로운 상태관리 라이브러리 도입

## Data Flow and Boundaries

### Backend

- `backend/api/app.py`
  - 요청/응답 진입점과 에러 매핑만 담당
- `backend/services/*_backend.py`
  - 특정 도메인 블록의 계산, payload shaping, file-to-response 변환 담당
- `backend/repositories/*`
  - 데이터 접근 seam 유지

원칙은 `엔드포인트는 thin`, `service는 focused`, `repository는 그대로`다.

### Frontend

- `frontend/app.js`
  - 앱 상태, 이벤트 wiring, runtime 조합 유지
- `frontend/*-runtime.js`
  - view-model 계산, markup builder, 도메인 렌더링 helper 담당

원칙은 `state orchestration은 app.js`, `render/view helper는 runtime`이다.

## Error Handling

- 새로 분리되는 service/runtime는 기존 예외 모델과 반환 포맷을 유지한다.
- 에러 메시지나 상태코드는 바꾸지 않는다.
- 프론트도 기존 DOM 업데이트 및 fallback 문구를 유지한다.

이번 작업의 목적은 동작 변경이 아니라 책임 분리이기 때문이다.

## Testing Strategy

각 분리 작업은 기존 테스트를 회귀 가드로 사용한다.

- backend:
  - 관련 API 테스트
  - 관련 단위 테스트가 있으면 그 파일 우선 실행
- frontend:
  - 문법 검사
  - 가능하면 기존 런타임 사용 패턴 기준의 최소 회귀 검증

분리 순서는 `이미 테스트로 고정된 영역 -> 테스트가 상대적으로 약한 영역` 순으로 진행한다.

## Execution Order

권장 실행 순서는 아래와 같다.

1. backend tracker export workbook
2. backend artifact preview
3. backend sales claim support
4. frontend tracker board/list rendering
5. frontend organization admin rendering
6. frontend sales summary/archive rendering
7. backend auth session cookie helpers

이 순서는 `응집도`, `기존 테스트 존재`, `현재 패턴과의 일치도`를 기준으로 정했다.

## Success Criteria

아래를 만족하면 이번 모듈화는 성공으로 본다.

1. `app.py`, `auth_runtime.py`, `app.js`가 의미 있게 줄어든다.
2. 새 파일이 기존 패턴과 동일한 네이밍/책임 구조를 가진다.
3. 공개 동작, 응답 계약, UI 동작은 바뀌지 않는다.
4. 관련 테스트와 검증 명령이 모두 통과한다.
5. 이후 추가 모듈화도 같은 패턴으로 이어갈 수 있는 구조가 된다.
