# 현재 구현 기준 재구축 시스템/기술 명세서

- 문서 역할: 시스템 설계 + 기술명세서
- 정본 여부: `canonical`
- 기준 커밋: `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238`
- 작성일: 2026-04-30
- 상위 기준 문서: [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./DOCUMENT_GOVERNANCE_MATRIX_KR.md)
- 기준 기능 문서: [REBUILD_FUNCTIONAL_SPEC_KR.md](./REBUILD_FUNCTIONAL_SPEC_KR.md)
- 목적: 현재 구현과 95% 이상 유사한 재구축을 위해 아키텍처, API, DB, 상태, 저장소, job, 외부 연동 기준을 고정한다.

## 1. 권장 아키텍처

권장 구성:

1. Frontend: 단일 웹 콘솔, 사용자 모드/관리자 모드 분기
2. Backend API: 인증 bridge, 실행, tracker, sales, admin, Google Sheets, artifact API
3. Worker/Service: pipeline 실행, tracker export, report job, download job
4. Database: Supabase Postgres 또는 동등한 RDB
5. Auth: Supabase Auth 또는 이메일/비밀번호 기반 동등 구현
6. File Storage: 현재 구현 호환 기준은 local filesystem artifact + DB metadata
7. External Integrations: Google Sheets, 공고 수집 source, 메일 발송 provider

## 2. 시스템 경계

### 2.1 Frontend 책임

1. 인증 상태와 shell 분기
2. home bootstrap 기반 초기 데이터 로딩
3. 실행 생성/상태 조회/로그 표시
4. tracker 목록, 상세, 수정
5. sales claim UI
6. 관리자 사용자/초대/감사/Google Sheets UI
7. 오류/빈 상태/권한 상태 표시

### 2.2 Backend API 책임

1. session 검증
2. membership/role 판정
3. run 생성/조회/취소
4. tracker read/write/effective model 제공
5. related notice snapshot read path 제공
6. sales claim transaction 처리
7. invitation/account/admin/audit 처리
8. artifact metadata와 file response 제공
9. Google Sheets snapshot/sync 제공

### 2.3 Worker/Service 책임

1. 공고 수집
2. native/synthetic pipeline 실행
3. tracker entry 생성
4. tracker export child run queue
5. report job 실행
6. download job 실행
7. artifact file 생성

## 3. 핵심 상태 모델

### 3.1 run status

필수 상태:

1. `queued`
2. `running`
3. `success`
4. `failed`
5. `canceled`

상태 전이:

1. `queued` -> `running`
2. `running` -> `success`
3. `running` -> `failed`
4. `queued` 또는 `running` -> `canceled`

### 3.2 account/membership status

계정 상태:

1. `active`
2. `inactive`
3. `disabled`

소속 상태:

1. `active`
2. `inactive`
3. `invited`
4. `removed`

계정 상태와 소속 상태는 분리한다. 계정은 살아 있어도 특정 조직 소속은 비활성일 수 있다.

### 3.3 sales status

영업 상태:

1. unclaimed
2. claimed
3. transferred
4. released
5. closed_won
6. closed_lost

저장 이벤트명:

1. `claim`
2. `note_update`
3. `transfer`
4. `release`
5. `force_release`
6. `close_won`
7. `close_lost`

## 4. API 기준

### 4.1 Auth API

현재 구현 기준 endpoint:

| 기능 | endpoint |
| --- | --- |
| 로그인 | `POST /api/auth/sign-in` |
| 가입 | `POST /api/auth/sign-up` |
| 로그아웃 | `POST /api/auth/sign-out` |
| 외부 session import | `POST /api/auth/session/import` |

`/login`, `/logout` 같은 단순 경로는 표준이 아니다. 필요하면 compatibility alias로만 둔다.

### 4.2 Run API

필수 기능:

1. run 생성
2. run 목록 조회
3. run 상세 조회
4. run 취소
5. run event/SSE
6. artifact 목록 조회
7. report job 생성/상태 조회

run response는 최소 아래 정보를 포함한다.

1. `run_id`
2. `run_type`
3. `status`
4. `progress`
5. `created_at`
6. `started_at`
7. `finished_at`
8. `error_json`
9. `parent_run_id`
10. `child_runs`

### 4.3 Tracker API

필수 기능:

1. tracker entry 목록 조회
2. tracker entry 상세 조회
3. editable field 수정
4. missing report 조회
5. cleanup preview/apply
6. contact resolution summary 조회
7. tracker template upload/reset
8. tracker download job 생성/상태/다운로드

현재 구현 기준:

1. `project_id`는 API/read model에서 제공하는 핵심 식별자다.
2. DB의 `tracker_entries` 물리 컬럼으로 반드시 저장한다는 뜻은 아니다.
3. 원본 값과 override 값을 분리하고 effective model을 응답한다.

### 4.4 Related Notice API

필수 기능:

1. 프로젝트별 관련 공고 조회
2. published snapshot 조회
3. cache 상태 표시
4. 관련 공고 원문 링크 제공

### 4.5 Sales API

현재 구현 기준 endpoint 형태:

`/api/sales-claims/projects/{project_id}/...`

필수 action:

1. claim
2. memo/note update
3. transfer
4. release
5. force release
6. close won
7. close lost
8. archive/list aggregation

`/api/sales-claims/{project_id}/...` 형태는 표준이 아니다. 필요 시 호환 alias로만 둔다.

### 4.6 Admin API

필수 기능:

1. organization bootstrap
2. user list
3. invitation create/revoke/list
4. membership role/status update
5. account status update
6. audit log list
7. platform admin account create
8. platform admin password reset

### 4.7 Google Sheets API

필수 기능:

1. sheets admin bootstrap
2. sheet list
3. sheet snapshot read
4. column filter metadata
5. sync trigger
6. sync status/result

## 5. DB 기준

### 5.1 핵심 테이블

권장 핵심 테이블:

1. `organizations`
2. `user_profiles`
3. `organization_memberships`
4. `invitations`
5. `audit_logs`
6. `runs`
7. `run_events`
8. `artifacts`
9. `tracker_entries`
10. `tracker_entry_overrides`
11. `tracker_change_events`
12. `related_notice_snapshots`
13. `sales_claims`
14. `sales_claim_events`
15. `download_audit_logs`

구현체가 동일 테이블명을 쓰지 않아도 되지만 위 도메인 데이터는 분리되어야 한다.

### 5.2 legacy users

기존 `users` 단일 테이블 모델은 최종 권한 모델로 쓰지 않는다.

현재 구현 호환상 legacy users가 존재할 수 있으나, 재구축 표준은 아래 조합이다.

1. auth identity
2. `user_profiles`
3. `organization_memberships`

### 5.3 artifact 저장

현재 구현 기준:

1. `artifacts` 테이블은 metadata를 저장한다.
2. 파일 본문은 local filesystem에 저장할 수 있다.
3. API는 metadata와 file path를 조합하여 preview/download를 제공한다.
4. Supabase Storage는 필수 MVP가 아니다.

### 5.4 sales transaction

sales action은 transaction으로 처리한다.

각 action은 아래를 함께 보장한다.

1. 현재 claim 상태 검증
2. actor 권한 검증
3. `sales_claims` 상태 갱신
4. `sales_claim_events` append
5. 필요한 경우 audit log append

## 6. tracker export child run 규칙

현재 구현 기준을 표준으로 삼는다.

1. parent run이 `project_tracker`이고 성공하면 `tracker_export` child run을 자동 생성 또는 재사용한다.
2. 같은 parent 아래 `queued`, `running`, `success` child가 있으면 재사용한다.
3. child run을 강제로 새로 만드는 기능은 후속 확장이다.
4. UI는 parent run과 child run 상태를 함께 보여준다.

## 7. home bootstrap

초기 화면 성능을 위해 home bootstrap API를 제공한다.

bootstrap 응답은 아래 slice를 포함한다.

1. current user
2. organization
3. memberships/roles
4. recent runs
5. latest report
6. artifact summary
7. tracker summary
8. sales summary
9. admin summary

일부 slice가 실패해도 전체 화면이 빈 화면이 되면 안 된다. 실패한 slice는 오류 상태와 재시도 수단을 제공한다.

## 8. job 모델

### 8.1 report job

현재 구현 호환:

1. memory queue 허용
2. file output 허용
3. 서버 재시작 시 job 상태 유실 가능성은 운영 제한으로 명시

장기 운영 개선:

1. 영속 job table
2. retry policy
3. job ownership
4. expiration cleanup

### 8.2 tracker download job

필수 상태:

1. `queued`
2. `running`
3. `success`
4. `failed`
5. `expired`

필수 응답:

1. job id
2. status
3. progress
4. file name
5. download URL 또는 download endpoint
6. error summary

## 9. native/synthetic/collect mode

수집/분석 실행은 mode를 가진다.

1. `native`: 실제 수집/분석 runtime 사용
2. `synthetic`: 개발/검증용 synthetic 데이터 사용
3. `collect`: 외부 source 수집 중심 실행

UI와 API는 mode를 표시하고, 진단 필드에 실행 방식과 source 정보를 남긴다.

## 10. 오류 응답 기준

공통 오류 응답은 아래 필드를 포함한다.

1. `code`
2. `message`
3. `detail`
4. `request_id`
5. `field_errors`

`error_json`은 run 실패 원인을 구조화하여 저장한다. UI는 원문 JSON 전체를 그대로 노출하기보다 요약과 상세 펼치기를 제공한다.

## 11. 외부 연동 기준

### 11.1 Google Sheets

1. API credential은 환경변수 또는 secret store에 둔다.
2. sheet snapshot은 cache/read path를 가진다.
3. sync 실패는 사용자에게 표시하고 audit/log에 남긴다.

### 11.2 메일

1. 초대 메일 자동 발송을 우선한다.
2. 발송 실패 시 링크 fallback을 제공한다.
3. SMTP provider는 교체 가능해야 한다.

### 11.3 공고 수집 source

1. source별 adapter를 분리한다.
2. raw response와 normalized record를 분리한다.
3. 수집 실패는 run error와 diagnostics에 기록한다.

## 12. 기술 검수 기준

1. endpoint 경로가 현재 구현 기준과 일치한다.
2. `tracker_entries.project_id`를 물리 컬럼으로 오해하지 않는다.
3. sales event type이 현재 구현 이벤트명과 일치한다.
4. artifact storage가 local file + DB metadata 기준으로 동작한다.
5. `project_tracker` 성공 후 `tracker_export` child run이 자동 queue/reuse 된다.
6. report/download job 상태가 UI와 API에서 일관된다.
7. home bootstrap partial failure가 전체 화면 장애로 번지지 않는다.

