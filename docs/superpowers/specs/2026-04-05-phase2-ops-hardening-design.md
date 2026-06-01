# Phase 2 Ops Hardening Design

**Goal**

`feature/related-notice-search` 브랜치를 회사 운영용 상위 버전으로 끌어올리기 위해, 문서상 남아 있는 우선순위 `1, 2, 3`을 실제 코드 경계에 맞게 정리한다. 이번 범위에서는 `Google 로그인 UX`와 `결제/청구 구현`은 제외한다.

## 배경

- 문서상 1순위는 `contact resolver v1 운영 반영`, `샘플 재추출 검증`, `백필 검증`, `오염 run 재발 방지`다.
- 문서상 2순위는 `sales claim UI와 실제 auth 사용자 연결 마무리`, `org 단위 접근 제어 강화`다.
- 문서상 3순위는 `org_admin 초대 UI`, `membership/role 관리 UI`, `한도 현황/플랜 요약 UI`, `회사별 감사 로그 화면`이다.
- 실제 코드상 3순위 화면과 API는 상당 부분 이미 존재한다. 반면 1순위의 관리자 정리 경로와 2순위의 tracker read/export 경계는 실질 갭으로 보인다.

## 설계 원칙

- 기존 거대 파일에 기능만 덧대지 않는다.
- 서비스 로직, 저장소 확장, API 연결, 프런트 UI 연결을 분리한다.
- 테스트 우선으로 구현한다.
- `Phase 3 billing`은 건드리지 않는다.
- `plan_code`, `active_user_limit`, `pending_invite_limit` 같은 운영 한도 구조는 유지한다.

## 범위

### 1. 오염 run 정리와 운영 검증 경로

- 관리자용 `tracker cleanup` 서비스 추가
- `source_tracker_run_id` 기준 tracker rows를 식별하고, 연결된 child `tracker_export` run과 부모 run까지 일괄 정리할 수 있는 경로 추가
- 관련 `pipeline_runs`, `pipeline_logs`, `run_artifacts` 삭제 기능을 저장소 계층에 추가
- dry-run과 apply를 분리해, 실제 삭제 전 영향 범위를 먼저 확인할 수 있게 한다

### 2. org 단위 접근 경계 보강

- auth가 활성화된 경우 `tracker-entries`, `tracker-entry-summaries`, export 계열 read endpoint도 조직 컨텍스트를 요구하도록 정리
- 기존 `SalesActor`와 `request.state.auth_context` 기반 경계를 재사용한다
- phase1 fallback은 유지하되, phase2 auth 활성화 상태에서는 무인증 tracker read가 우회 경로가 되지 않도록 막는다

### 3. 운영 UI 모듈 분리

- 이미 있는 조직 운영 화면을 새로 만들지 않고, `app.js`에 묶여 있는 조직 관리자 UI를 분리한다
- 대상은 초대, 사용자/권한 관리, 감사 로그, 플랜 요약 영역이다
- 데이터 로딩은 기존 `console-data-runtime.js`를 최대한 재사용하고, 렌더링/이벤트 바인딩만 별도 런타임으로 뺀다

## 비범위

- Google 로그인 연결 UX
- 결제, checkout, webhook, billing transaction
- SSO 실제 연동
- 승인 흐름과 고급 집계 전체

## 아키텍처

### 백엔드

- `backend/services/tracker_cleanup_backend.py`
  - cleanup 대상 계산
  - dry-run 결과 생성
  - apply 시 삭제 순서 조정
- `backend/services/tracker_access_backend.py`
  - auth 활성화 여부와 request auth context를 기준으로 tracker read 접근 허용 여부 계산
- 저장소 프로토콜 확장
  - `RunRepository.delete_run`
  - `RunLogRepository.delete_logs_for_run`
  - `ArtifactRepository.delete_artifacts_for_run`

### 프런트엔드

- `frontend/organization-admin-runtime.js`
  - 조직 운영 탭 렌더링 보조
  - 초대 폼/사용자 목록/감사 로그/플랜 요약 이벤트 연결
- `frontend/app.js`
  - 조립만 담당
  - 분리된 런타임을 require/load 하는 접점만 유지

## 데이터 흐름

### tracker cleanup

1. 관리자가 특정 `source_tracker_run_id` 또는 parent run id 기준으로 cleanup preview 요청
2. 서비스가 tracker rows, child run, parent run, logs, artifacts 존재 여부를 수집
3. preview 응답으로 삭제 예정 건수와 대상 id 목록을 반환
4. 관리자가 apply 요청
5. 서비스가 artifacts -> logs -> child run -> tracker rows 영향 제거 -> parent run 순으로 정리
6. 결과를 audit-friendly payload로 반환

### tracker access

1. tracker read endpoint 진입
2. auth 활성화 여부 확인
3. auth 활성화 시 request auth context와 organization_id 확보
4. 해당 organization 기준 저장소/응답 경계 적용

## 테스트 전략

- 저장소 계층 delete 동작 단위 테스트
- cleanup backend dry-run/apply 단위 테스트
- cleanup API 권한/preview/apply API 테스트
- tracker read endpoint auth scope 테스트
- organization admin runtime 분리 후 smoke 수준 DOM/호출 테스트 또는 기존 JS 함수 단위 테스트

## 성공 기준

- 문서에만 남아 있던 `관리자용 정리 루트`가 실제 API와 서비스로 존재한다
- auth 활성화 상태에서 tracker read/export가 조직 경계를 우회하지 않는다
- 조직 운영 UI 코드가 `app.js`에서 분리되어 기능을 유지한다
- 기존 auth invitation / users / audit / sales claim 테스트가 깨지지 않는다
