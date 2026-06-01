# 재구축 구현 플레이북

- 문서 역할: 재구축 구현 플레이북
- 정본 여부: `canonical`
- 이 문서가 답하는 질문: 현재 정본 문서 체계를 기준으로 어떤 순서와 모듈 경계로 시스템을 다시 구현해야 하는가
- 이 문서가 답하지 않는 질문: 개별 API 필드 전체 목록, 개별 DB 컬럼의 모든 제약, 과거 실험 기록
- 상위 기준 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md), [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md), [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md), [TECHNICAL_SPEC_KR.md](./TECHNICAL_SPEC_KR.md), [OPERATIONS_POLICY_KR.md](./OPERATIONS_POLICY_KR.md), [UI_SCREEN_SPEC_KR.md](./UI_SCREEN_SPEC_KR.md)
- 충돌 시 우선 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)

작성일: 2026-03-22  
상태: 통합 초안 v1

## 1. 문서 목적

이 문서는 `무엇을 만들어야 하는가`가 아니라 `어떤 순서와 단위로 다시 만들어야 하는가`를 고정한다.

목적은 세 가지다.

1. 재구축 착수 순서를 고정한다.
2. 백엔드/프론트엔드/DB/Auth 모듈 경계를 고정한다.
3. 화면, API, DB, 상태 모델을 어느 단계에서 연결해야 하는지 실무 순서로 설명한다.

이 문서는 `문서만 보고 95% 이상 구현 가능`을 목표로 하므로, 단순 개요가 아니라 아래를 포함한다.

- 구현 단계 순서
- 단계별 선행조건과 종료조건
- 모듈 분해 기준
- 화면-API-DB 매핑
- stub/mock 허용 범위
- 최종 수용 체크리스트

## 2. 이 플레이북을 읽는 순서

재구축 담당자는 아래 순서로 문서를 읽는다.

1. [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)
2. [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md)
3. [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md)
4. [TECHNICAL_SPEC_KR.md](./TECHNICAL_SPEC_KR.md)
5. [OPERATIONS_POLICY_KR.md](./OPERATIONS_POLICY_KR.md)
6. [UI_SCREEN_SPEC_KR.md](./UI_SCREEN_SPEC_KR.md)
7. 본 문서

실제 구현 중 세부 계약이 필요하면 아래 reference를 참고한다.

- [reference/contracts/api-spec.md](../reference/contracts/api-spec.md)
- [reference/contracts/db-schema.md](../reference/contracts/db-schema.md)
- [reference/contracts/job-lifecycle.md](../reference/contracts/job-lifecycle.md)
- [reference/contracts/request-response-examples.md](../reference/contracts/request-response-examples.md)
- [reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md](../reference/rebuild/REBUILD_GOLDEN_SCENARIOS_KR.md)
- [reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md](../reference/rebuild/SCREEN_API_DB_FIELD_MAPPING_KR.md)
- [reference/rebuild/UI_STATE_MATRIX_KR.md](../reference/rebuild/UI_STATE_MATRIX_KR.md)

## 3. 재구축 기본 원칙

1. 기능 요구사항은 [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md)를 기준으로 본다.
2. 시스템 경계와 책임 분리는 [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md)를 기준으로 본다.
3. API/DB/상태/이벤트 계약은 [TECHNICAL_SPEC_KR.md](./TECHNICAL_SPEC_KR.md)를 기준으로 본다.
4. 권한, 초대, 계정상태, 삭제정책, 영업 이관, 메일 정책은 [OPERATIONS_POLICY_KR.md](./OPERATIONS_POLICY_KR.md)를 기준으로 본다.
5. 실제 화면 구조와 노출 규칙은 [UI_SCREEN_SPEC_KR.md](./UI_SCREEN_SPEC_KR.md)를 기준으로 본다.
6. 구현 중 문서 충돌이 나면 항상 [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)의 우선순위를 따른다.

## 4. 재구축 범위 정의

이 플레이북이 대상으로 삼는 구현 범위는 아래와 같다.

### 4.1 포함 범위

1. Supabase Auth 기반 로그인/로그아웃
2. `platform_admin`, `org_admin`, `org_member` 구조
3. `user_profiles`, `organization_memberships`, `invitations`, `audit_logs`
4. `project_tracker`, `tracker_export` 실행 흐름
5. tracker entries 조회/수정/effective model
6. 영업 claim/transfer/release/close/메모 append 흐름
7. 사용자 모드/관리자 모드 UI
8. 엑셀 다운로드
9. 초대 기반 사용자 생성
10. 회원정보 수정

### 4.2 의도적으로 미루는 범위

1. `seats` 물리 테이블
2. 회사 SSO
3. SCIM
4. 세분 퍼미션 매트릭스
5. 조직도/부서 트리
6. 관리자별 별도 세션 TTL

## 5. 권장 구현 순서

아래 순서를 바꾸지 않는 것을 권장한다.

### 5.1 0단계: 개발 기반 세팅

구축 대상:

1. 프로젝트 구조
2. 환경변수 로더
3. Supabase 연결 설정
4. 로컬 개발 서버 기동 구조
5. 기본 health endpoint

종료 조건:

1. API 서버가 `/health`에 `200` 응답
2. `.env` 또는 배포 환경변수에서 Supabase 설정을 읽음
3. 프론트 정적 자산 서빙 가능

### 5.2 1단계: 인증 골격

구축 대상:

1. Supabase Auth 연결
2. 세션 쿠키 저장
3. `GET /api/auth/session`
4. `POST /api/auth/login`
5. `POST /api/auth/logout`
6. bootstrap `platform_admin`

종료 조건:

1. 로그인 전엔 콘솔이 보이지 않음
2. 로그인 후 세션 정보, 역할, 권한 여부를 해석 가능
3. 로그아웃 시 즉시 보호 화면으로 되돌아감

### 5.3 2단계: 프로필/소속/초대

구축 대상:

1. `user_profiles`
2. `organization_memberships`
3. `invitations`
4. `audit_logs`
5. invitation accept transaction

종료 조건:

1. 초대 생성/수락/철회/만료 흐름이 동작
2. 같은 초대를 중복 수락해도 membership이 중복 생성되지 않음
3. `platform_admin`와 조직 역할이 분리돼 있음

### 5.4 3단계: 실행(run) 엔진

구축 대상:

1. `POST /api/runs`
2. `GET /api/runs`
3. `GET /api/runs/{run_id}`
4. `POST /api/runs/{run_id}/cancel`
5. `GET /api/runs/{run_id}/logs`
6. `GET /api/runs/{run_id}/artifacts`
7. `POST /api/runs/{run_id}/tracker-export`

종료 조건:

1. `project_tracker`와 `tracker_export`가 부모/자식 run으로 분리 동작
2. 진행률, 상태, 로그, 산출물을 API에서 일관되게 조회 가능
3. child run 실패가 parent run 상태를 직접 뒤집지 않음

### 5.5 4단계: tracker 읽기/쓰기 계층

구축 대상:

1. tracker entries 조회
2. tracker effective value 규칙
3. tracker override 저장
4. audit log 연동
5. 프로젝트 집계/검색

종료 조건:

1. GUI parity에 필요한 tracker 핵심 필드가 웹에서 일관되게 보임
2. 수정 후 effective view와 audit log가 동시에 갱신됨
3. 프로젝트 현황 보드가 동작함

### 5.6 5단계: 영업 파이프라인

구축 대상:

1. `project_sales_claims`
2. `project_sales_claim_events`
3. claim / transfer / release / close
4. 메모 append-only 히스토리
5. 종료/완료 정리
6. 사용자/관리자 읽기 모델

종료 조건:

1. 한 프로젝트는 한 시점에 한 담당자만 claim 가능
2. 담당 변경은 release보다 transfer 중심으로 동작
3. 계약 완료/영업 종료가 별도 상태로 정리됨
4. 사용자 모드와 관리자 모드 읽기 모델이 일관됨

### 5.7 6단계: 사용자 홈/관리자 홈 UI

구축 대상:

1. 사용자 모드 홈
   - 내가 진행 중인 영업
   - 회사 전체 진행 중인 영업
   - 전체 영업 대상 프로젝트
2. 관리자 모드 홈
   - 영업사원별 진행 현황
   - 종료/완료 정리
   - 사용자 초대 및 관리

종료 조건:

1. 사용자 모드에서는 영업현황 수정 가능 영역과 읽기 전용 영역이 정확히 분리됨
2. 관리자 모드에서는 초대, 사용자 관리, 진행 현황 집계가 가능
3. 사용자 모드에서는 실행 상세 등 운영 패널이 노출되지 않음

### 5.8 7단계: 다운로드/메일/마감 polish

구축 대상:

1. 영업 목록 엑셀 다운로드
2. tracker export workbook 다운로드
3. 메일 발송 공급자 연결
4. 세션 장기 유지
5. UI 문구/모달/prompt 치환

종료 조건:

1. 다운로드가 템플릿 기반으로 일관되게 생성됨
2. 초대 메일 또는 fallback 링크 전달이 가능
3. 장시간 로그인 유지가 동작

## 6. 권장 백엔드 모듈 분해

### 6.1 API 레이어

- `backend/api/app.py`
  - 라우트 등록
  - 의존성 조합
  - 응답 포맷 정리

- `backend/api/auth_runtime.py`
  - 세션 해석
  - 로그인/로그아웃
  - 프로필 갱신
  - invitation accept context

- `backend/api/schemas.py`
  - 요청/응답 스키마
  - enum/DTO

### 6.2 Repository 레이어

- `backend/repositories/`
  - tracker repository
  - run repository
  - artifact repository
  - log repository
  - sales claim repository
  - auth/profile/membership/invitation repository

원칙:

1. 모든 저장소는 `supabase`와 `in_memory`를 동일 인터페이스로 구현한다.
2. 저장소는 도메인 규칙을 많이 먹지 않는다.
3. 도메인 규칙은 service 계층으로 밀어낸다.

### 6.3 Service 레이어

- `run_execution`
- `tracker_export`
- `sales_claims`
- `invitations`
- `profile_membership_management`

원칙:

1. 상태 전이와 트랜잭션 규칙은 service 계층에서 관리한다.
2. `claim -> note append -> transfer -> close` 흐름은 repository가 아니라 service에서 보장한다.
3. invitation accept는 반드시 idempotent + transaction으로 처리한다.

## 7. 권장 프론트엔드 모듈 분해

현재는 단일 파일 비중이 크더라도, 재구축 시에는 아래 경계를 권장한다.

1. auth shell
2. header/meta
3. dashboard summary
4. run form
5. run detail
6. recent runs
7. project/tracker board
8. user sales home
9. admin sales panels
10. invitation and user management
11. profile modal
12. shared modal/flash/format utilities

원칙:

1. 사용자 모드/관리자 모드 차이는 `렌더링 조건`으로만 덮지 말고 섹션 경계로도 분리한다.
2. 영업 도메인 UI는 `my/company/target/closed` 4분할 읽기 모델을 유지한다.
3. 입력 모달, 계약금액 모달, flash 메시지, 다운로드 유틸은 공통 모듈로 뺀다.

## 8. 화면-API-DB 매핑

### 8.1 로그인/회원정보

| 화면 | API | DB/외부 |
| --- | --- | --- |
| 로그인 shell | `POST /api/auth/login` | Supabase Auth |
| 세션 유지 | `GET /api/auth/session` | Supabase Auth + app cookie |
| 로그아웃 | `POST /api/auth/logout` | app cookie |
| 회원정보 수정 | `PATCH /api/auth/profile` | `user_profiles`, Supabase Auth password |

### 8.2 사용자 초대 및 관리

| 화면 | API | DB |
| --- | --- | --- |
| 사용자 초대 | `POST /api/auth/invitations` | `invitations`, `audit_logs` |
| 초대 목록 | `GET /api/auth/invitations` | `invitations` |
| 초대 철회 | `POST /api/auth/invitations/revoke` | `invitations`, `audit_logs` |
| 사용자 목록 | `GET /api/auth/users` | `user_profiles`, `organization_memberships` |
| 역할/상태 수정 | `PATCH /api/auth/users/{id}` 성격 endpoint | `organization_memberships`, `audit_logs` |

### 8.3 실행/트래커

| 화면 | API | DB/스토리지 |
| --- | --- | --- |
| 실행 생성 | `POST /api/runs` | `pipeline_runs` |
| 실행 상세 | `GET /api/runs/{id}` | `pipeline_runs` |
| 로그 | `GET /api/runs/{id}/logs` | `pipeline_logs` |
| 아티팩트 | `GET /api/runs/{id}/artifacts` | `run_artifacts`, local/supabase storage |
| tracker export | `POST /api/runs/{id}/tracker-export` | `pipeline_runs`, workbook artifact |
| tracker 보드 | `GET /api/tracker-entries` | effective tracker view |
| tracker 수정 | `PATCH /api/tracker-entries/{id}` | override + audit |

### 8.4 영업 파이프라인

| 화면 | API | DB |
| --- | --- | --- |
| 내가 진행 중인 영업 | `GET /api/sales-claims` | `project_sales_claims`, events |
| 회사 전체 진행 중인 영업 | `GET /api/sales-claims` | same read model |
| 전체 영업 대상 프로젝트 | `GET /api/tracker-entry-summaries` 성격 | tracker effective view |
| 영업 시작 | `POST /api/sales-claims/{project_id}/claim` | claims + events |
| 메모 저장 | `PATCH /api/sales-claims/{project_id}` | events |
| 담당 이관 | `POST /api/sales-claims/{project_id}/transfer` | claims + events + audit |
| 해제 | `POST /api/sales-claims/{project_id}/release` | claims + events |
| 계약 완료/영업 종료 | `POST /api/sales-claims/{project_id}/close` | claims + events |
| 영업 집계 | `GET /api/sales-claims/summary-by-user` | claims/events read model |
| 엑셀 다운로드 | `GET /api/sales-claims/export` | workbook build |

## 9. 단계별 구현 완료 기준

### 9.1 인증

- 로그인 shell이 뜬다
- 로그인 후 세션이 유지된다
- 로그아웃이 동작한다
- 현재 비밀번호 확인 후 회원정보 수정이 된다

### 9.2 초대/사용자 관리

- 자기 자신 초대가 차단된다
- 초대 이메일과 로그인 이메일 불일치가 차단된다
- 철회된 초대는 활성 목록에서 빠진다
- 조직 역할과 계정 상태가 분리되어 반영된다

### 9.3 실행/트래커

- `project_tracker` 실행 생성/조회/취소 가능
- child `tracker_export` 자동/수동 트리거 가능
- tracker 보드와 수정이 동작
- workbook 다운로드 가능

### 9.4 영업 파이프라인

- 같은 프로젝트 중복 claim이 막힌다
- 메모는 append-only로 쌓인다
- transfer가 release보다 우선 시나리오다
- 계약 완료 시 계약금액이 필수다
- 종료/완료 정리에서 연도/월 그룹화가 된다

### 9.5 UI

- 사용자 모드에서 운영 패널이 숨겨진다
- 관리자 모드에서만 초대/사용자 관리가 보인다
- `내가 진행 중인 영업`과 `회사 전체 진행 중인 영업`은 좌우 2열로 정렬된다
- `전체 영업 대상 프로젝트`에는 미배정 신규 대상만 남는다

## 10. 재구축 중 허용되는 stub/mock

아래는 초기 단계에서 임시 stub가 허용된다.

1. 메일 발송 공급자
   - 실제 SMTP 미연결 시 링크 복사 fallback
2. 외부 collect API
   - synthetic 또는 샘플 데이터 기반 smoke test
3. read model 캐시
   - 초기에는 직접 집계 후 추후 최적화 가능

단, 아래는 stub로 오래 두면 안 된다.

1. invitation accept transaction
2. membership 상태 체크
3. sales claim owner 중복 방지
4. tracker effective value 규칙

## 11. 가장 위험한 드리프트 포인트

재구축 중 아래는 반드시 일치시켜야 한다.

1. `platform_admin`와 조직 역할을 섞지 말 것
2. `user_profiles`와 `organization_memberships`를 합치지 말 것
3. `project_id` 기준 claim 잠금을 `entry_id`로 바꾸지 말 것
4. 메모 삭제 정책을 임의로 완화하지 말 것
5. `전체 영업 대상 프로젝트`에 진행 중/종료/완료 프로젝트를 다시 넣지 말 것
6. invitation accept를 transaction 없이 구현하지 말 것

## 12. 최종 체크리스트

아래 항목을 모두 만족하면 `문서 기준 재구축 성공`으로 본다.

1. 인증, 초대, membership, profile이 문서 기준대로 동작
2. 실행(run), tracker export, workbook 다운로드가 동작
3. tracker 보드와 effective view가 문서 기준대로 동작
4. 영업 claim/transfer/close와 메모 append 정책이 동작
5. 사용자 모드/관리자 모드 분기가 문서 기준대로 동작
6. 정본 `00~07`만 읽고 구현 순서와 화면/API/DB 연결을 설명할 수 있다

## 13. 결론

재구축은 `화면부터`가 아니라 아래 순서를 지켜야 안정적이다.

1. 기반 인프라
2. Auth/Profile/Membership/Invitation
3. Run/Tracker
4. Sales Claim
5. UI 조립
6. Mail/Download/Polish

이 문서의 목적은 `무엇을 만드는가`가 아니라 `어떻게 다시 만들 것인가`를 고정하는 것이다.

