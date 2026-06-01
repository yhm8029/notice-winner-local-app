# 현재 구현 기준 갭 리포트 및 재구축 통합 명세서

- 문서 역할: origin/main 현재 구현 기준 갭 리포트 + 재구축 기능/화면/API/운영 명세 초안
- 기준 커밋: `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238`
- 작성일: 2026-04-29
- 목적: 기존 코드 없이도 새 구현팀이 현재 웹 콘솔과 약 95% 이상 유사한 기능/동작/화면을 재구현할 수 있도록 요구사항을 통합한다.
- 적용 원칙: 기존 canonical/reference 문서와 충돌하면 이 문서의 "현재 구현 기준 표준"을 우선한다.
- 제외: 실제 회사 데이터, 운영 계정 비밀, API key, 배포 서버 비밀, 기존 소스 코드 복제 지시.

## 1. 문서 사용 방법

이 문서는 기존 정본 6개 문서를 대체하기보다, 현재 구현과 문서 간 차이를 반영한 재구축용 상위 초안이다.

재구축 담당자는 아래 순서로 읽는다.

1. 본 문서의 갭 리포트와 현재 구현 기준 표준을 먼저 확인한다.
2. 기능과 화면은 `FUNCTIONAL_SPEC_KR.md`, `UI_SCREEN_SPEC_KR.md`가 아니라 본 문서의 보강 항목까지 포함해 구현한다.
3. API/DB는 `TECHNICAL_SPEC_KR.md`, `reference/contracts/*.md`를 그대로 따르지 말고 본 문서의 실제 구현 경로와 데이터 계약을 우선한다.
4. 운영정책은 `OPERATIONS_POLICY_KR.md`를 기본값으로 삼되, hard delete, 초대 idempotency, 이벤트명, 플랫폼 관리자 범위 등 충돌 항목은 본 문서의 결정을 따른다.

## 2. 현재 구현 기준 핵심 결론

현재 구현은 기존 정본 문서의 큰 줄기를 따르지만, 2026년 4월 기준으로 아래 기능이 정본 문서보다 앞서 있다.

1. Google Sheets 관리자 화면과 동기화/시트 조회/컬럼 필터
2. 관리자 상단 탭과 일부 legacy route alias
3. 실행 프리셋, home bootstrap snapshot/cache, tracker download job/warm
4. tracker template upload/reset
5. tracker change event, missing report, cleanup preview/apply, contact resolution summary
6. related notice published snapshot/cache/publication
7. platform admin 계정 생성과 사용자 비밀번호 초기화
8. login audit log, download audit log, 조직 감사 로그 slice bootstrap
9. report jobs, artifact preview, SSE run events

따라서 새 명세는 기존 문서의 기능 목록에 위 항목을 반드시 추가해야 한다.

## 3. 우선 갭 리포트

### 3.1 인수 전 반드시 명세에 고정할 항목

| 항목 | 현재 구현 | 기존 문서와 차이 | 재구축 표준 |
| --- | --- | --- | --- |
| Auth endpoint | `/api/auth/sign-in`, `/sign-up`, `/sign-out`, `/session/import` | 일부 문서가 `/login`, `/logout`로 표기 | 실제 구현 경로를 표준으로 삼는다. 호환 alias는 선택 사항이다. |
| Sales endpoint | `/api/sales-claims/projects/{project_id}/...` | 일부 문서가 `/api/sales-claims/{project_id}/...`로 표기 | 실제 구현 경로를 표준으로 삼는다. |
| Tracker export child run | 같은 parent의 `queued/running/success` child run 재사용 | 문서는 항상 새 child run 생성처럼 읽힘 | 재사용을 표준으로 삼고 `force_new`는 후속 확장으로 둔다. |
| 자동 tracker export | `project_tracker` 성공 후 자동 queue | 문서에는 수동 후처리 중심 | 자동 queue + 수동 요청 재사용을 모두 명시한다. |
| `tracker_entries.project_id` | DB 저장 컬럼이 아니라 API/read model 파생값 | DB 계약에는 저장 컬럼처럼 표기 | 파생값으로 명시한다. |
| Sales event type | `claim`, `note_update`, `transfer`, `release`, `force_release`, `close_won`, `close_lost` | 문서 이벤트명이 일부 다름 | 구현 이벤트명을 표준으로 삼는다. |
| Artifact storage | metadata는 DB, 파일 본문은 local filesystem | 일부 설계 문서가 Supabase Storage를 암시 | 현재 표준은 local artifact file + DB metadata다. |
| Related notice | published snapshot/cache/read path 있음 | 기능 문서에는 "관련 공고 열기" 수준 | snapshot/publication 계약을 별도 도메인으로 명시한다. |

### 3.2 제품 정책 결정을 명시해야 하는 항목

| 항목 | 현재 구현 | 재구축 결정 |
| --- | --- | --- |
| Google login | 기본 구현은 이메일/비밀번호 + Supabase token import | MVP 제외, 후속 확장으로 둔다. |
| hard delete | 사용자 삭제 API가 실제 연관 데이터 삭제를 수행 | 현행 호환 기능으로 문서화하되 운영 기본은 비활성화/소속 해제다. |
| 초대 메일 | 조건 충족 시 background 발송, 항상 link fallback 제공 | 자동 발송 우선 + 수동 fallback을 표준으로 둔다. |
| platform admin 범위 | 현재 세션의 organization 범위에서 동작 | 조직 전환 UI/API 전까지 현재 조직 범위로 제한한다. |
| run preset 저장 | DB 테이블은 있으나 구현은 memory store | 현행 호환은 memory store, 제품화 시 DB 저장으로 확장한다. |
| report job 저장 | memory job queue + file output | 현행 호환은 memory queue, 장기 운영은 영속 job table을 후속 과제로 둔다. |

## 4. 사용자 역할과 권한

### 4.1 역할

역할은 3개로 고정한다.

1. `platform_admin`
2. `org_admin`
3. `org_member`

권한 판정은 전역 역할과 조직 멤버십의 조합으로 수행한다.

- `platform_admin`: 전역 운영자 플래그를 가진 사용자다. 단, 현재 구현의 API는 모든 조직을 자유롭게 전환하지 않고 현재 세션의 `organization_id` 범위에서 동작한다.
- `org_admin`: 자기 조직의 사용자/초대/감사/영업 운영 기능을 가진 관리자다.
- `org_member`: 일반 사용자다. 사용자 모드와 본인 영업 업무를 수행한다.

참조 구현:

- `backend/api/routers/auth.py`
- `backend/api/routers/admin.py`
- `backend/api/support/auth_runtime_core.py`
- `frontend/app-support-org-runtime.js`
- `frontend/auth-session-runtime.js`

### 4.2 역할별 기능 범위

`platform_admin`은 아래를 수행할 수 있어야 한다.

1. 관리자 모드 진입
2. `org_admin`, `org_member` 초대
3. 조직 운영 패널 조회
4. platform admin 계정 직접 생성
5. 사용자 비밀번호 관리자 재설정
6. 사용자 역할/소속/팀/직책 변경
7. 영업 강제 이관/강제 해제/강제 종료
8. 최근 영업 메모 강제 수정
9. Google Sheets 관리자 패널 조회/동기화
10. tracker 진단/cleanup/backfill conflict 관리

`org_admin`은 아래를 수행할 수 있어야 한다.

1. 관리자 모드 진입
2. `org_member` 초대
3. 초대 목록 조회/철회
4. 조직 사용자 목록 조회
5. 사용자 역할/소속/팀/직책 변경
6. 조직 감사/로그인/다운로드 로그 조회
7. 영업사원별 진행 현황 조회
8. 영업 강제 이관/해제/종료
9. tracker 관리자 보드 조회/수정

`org_member`는 아래를 수행할 수 있어야 한다.

1. 로그인/로그아웃
2. 회원정보 수정
3. 사용자 모드 홈 조회
4. 본인 영업 시작/메모/이관/계약완료/영업종료/해제
5. 회사 전체 진행 중 영업 읽기 전용 조회
6. 전체 영업 대상 프로젝트 조회
7. 연관 공고/공고문 열기
8. 활성 사용자 목록 조회. 단, 비활성 사용자 포함 조회는 금지한다.

서버는 UI 노출 여부와 무관하게 모든 관리자 API에서 권한을 다시 확인해야 한다.

## 5. 인증, 초대, 계정 관리

### 5.1 인증 상태와 shell 전환

단일 진입점은 `/` 또는 `/app/`이다. 로그인 전과 로그인 후는 같은 정적 앱 안에서 shell만 전환한다.

`GET /api/auth/session` 응답에 따라 UI를 전환한다.

1. `enabled=false`: 인증 보호 없이 콘솔을 열 수 있다.
2. `authenticated=false`: 로그인/가입 shell만 표시한다.
3. `authenticated=true`, `authorized=false`: 접근 차단 패널만 표시한다.
4. `authenticated=true`, `authorized=true`: 콘솔 shell을 표시한다.

로그인 shell은 아래 요소를 포함한다.

1. 로그인/계정 등록 탭
2. 이메일 입력
3. 비밀번호 입력
4. 표시 이름 입력. 가입 모드에서 사용한다.
5. 초대 토큰 preview 영역
6. 아이디 안내 또는 로그인 도움 문구
7. 비밀번호 재설정 요청
8. 상태/오류 메시지
9. 차단 상태 로그아웃 버튼

초대 토큰이 URL에 있으면 초대 preview를 먼저 불러오고 이메일 입력을 초대 이메일로 고정한다.

참조 구현:

- `frontend/index.html`
- `frontend/auth-controller.js`
- `frontend/auth-ui-controller.js`
- `frontend/auth-session-runtime.js`
- `backend/api/routers/auth.py`

### 5.2 Auth API

표준 endpoint는 아래와 같다.

| 기능 | Method | Path |
| --- | --- | --- |
| 세션 조회 | GET | `/api/auth/session` |
| 외부 토큰 세션 import | POST | `/api/auth/session/import` |
| 로그인 | POST | `/api/auth/sign-in` |
| 가입 | POST | `/api/auth/sign-up` |
| 로그아웃 | POST | `/api/auth/sign-out` |
| 비밀번호 재설정 메일 | POST | `/api/auth/password-reset` |
| 회원정보 수정 | PATCH | `/api/auth/profile` |
| 초대 preview | GET | `/api/auth/invitations/preview` |
| 이메일 기반 초대 preview | GET | `/api/auth/invitations/preview-by-email` |
| 초대 수락 | POST | `/api/auth/invitations/accept` |
| 초대 목록 | GET | `/api/auth/invitations` |
| 초대 생성 | POST | `/api/auth/invitations` |
| 초대 철회 | POST | `/api/auth/invitations/{invitation_id}/revoke` |
| 조직 사용자 목록 | GET | `/api/auth/users` |
| 사용자 상태 변경 | PATCH | `/api/auth/users/{user_id}/status` |
| 사용자 소속/역할 변경 | PATCH | `/api/auth/users/{user_id}` |
| 사용자 계정 삭제 | DELETE | `/api/auth/users/{user_id}` |
| 조직 감사 로그 | GET | `/api/auth/audit-logs` |

기존 문서의 `/api/auth/login`, `/api/auth/logout`는 재구축 표준이 아니다.

### 5.3 세션 정책

세션은 signed cookie `tracker_auth_session`에 저장한다.

필수 동작:

1. cookie는 `HttpOnly`, `SameSite=Lax`로 설정한다.
2. 현재 구현 호환 기준으로 개발/초기 운영에서는 `secure=false`를 허용한다.
3. 기본 수명은 약 30일이다.
4. access token이 만료 임박하면 refresh token으로 갱신한다.
5. `/api/auth/session/import`는 bearer access token을 검증한 뒤 같은 cookie 세션으로 전환한다.
6. `/api/auth/sign-out`은 Supabase sign-out 실패 여부와 무관하게 cookie를 제거한다.
7. 단일 활성 세션 강제는 현재 표준에 포함하지 않는다.

### 5.4 가입과 초대 수락

초대 기반 가입이 기본이다. bootstrap platform admin 이메일은 예외적으로 최초 운영자 등록을 허용한다.

초대 정책:

1. 초대 생성은 관리자만 가능하다.
2. `platform_admin`은 `org_admin`, `org_member` 초대가 가능하다.
3. `org_admin`은 `org_member`만 초대할 수 있다.
4. 자기 자신 이메일 초대는 UI와 API 모두 차단한다.
5. 만료일은 1일부터 30일 사이로 제한하고 기본값은 7일이다.
6. 초대 이메일과 실제 로그인/가입 이메일은 반드시 일치해야 한다.
7. 초대 수락은 로그인된 세션이 필요하다.
8. 토큰이 없으면 같은 이메일의 pending 초대를 자동 탐색할 수 있다.
9. 같은 이메일 pending 초대가 여러 개면 ambiguous 오류로 차단한다.
10. revoked, expired, accepted-by-other 상태는 수락을 차단한다.

초대 preview 응답은 아래 정보를 포함해야 한다.

1. 조직명
2. 초대 이메일
3. 역할
4. 표시 이름
5. 팀명
6. 직책
7. 만료일
8. 상태
9. 초기 비밀번호 또는 안내 문구

### 5.5 플랜/초대 한도

플랜 기본값은 아래와 같다.

| Plan | active 사용자 한도 | pending 초대 한도 |
| --- | ---: | ---: |
| A | 5 | 5 |
| B | 10 | 10 |
| C | 100 | 100 |

조직별 override 컬럼이 있으면 override를 우선한다.

한도 계산:

1. 활성 사용자는 `account_status=active`이고 `membership_status=active`인 조직 사용자다.
2. `platform_admin`은 좌석 계산에서 제외한다.
3. pending 초대는 초대 한도에 포함한다.
4. 초대 생성 시 active 한도와 pending 한도를 모두 확인한다.
5. 초대 수락 시 active 한도를 다시 확인한다.

UI는 현재 사용량, 한도, 남은 수, 업그레이드 필요 여부를 보여준다.

### 5.6 초대 메일과 fallback

메일 발송은 아래 방식으로 동작해야 한다.

1. 환경 설정이 충족되면 초대 생성 후 background task로 메일 발송을 queue한다.
2. 메일 발송 조건이 없거나 실패하면 수동 전달 fallback을 제공한다.
3. UI는 초대 링크와 초기 비밀번호 복사를 항상 제공한다.
4. 발송 성공/실패는 관리자에게 명확히 알려야 한다.
5. 현재 구현 호환 기준에서는 `invite_mail_sent` 감사 이벤트는 필수가 아니다. 단, 후속 개선 후보로 둔다.

### 5.7 회원정보 수정

사용자는 본인 회원정보 모달에서 아래를 확인/수정한다.

읽기 전용:

1. 이메일
2. 회사명
3. 역할
4. 계정/소속 상태

수정 가능:

1. 표시 이름
2. 휴대폰
3. 회사 전화
4. 새 비밀번호

저장 조건:

1. 일반 수정은 현재 비밀번호 확인이 필요하다.
2. 초대 수락 후 24시간 이내 첫 비밀번호 설정은 `invite_token`으로 현재 비밀번호 없이 허용할 수 있다.
3. 새 비밀번호는 8자 이상이어야 한다.
4. 저장 후 세션 payload와 cookie를 갱신한다.

### 5.8 조직 사용자 관리

관리자는 조직 사용자 목록에서 아래 항목을 볼 수 있어야 한다.

1. 표시 이름
2. 이메일
3. 계정 상태
4. 소속 상태
5. 역할
6. 팀명
7. 직책
8. 저장 버튼
9. 삭제 버튼

변경 규칙:

1. 관리자만 변경 가능하다.
2. bootstrap/platform admin 계정은 역할/상태/삭제가 잠긴다.
3. 자기 자신의 역할/상태/삭제는 잠긴다.
4. 팀명/직책은 보호 계정이라도 현행 구현 기준으로 수정 가능 영역으로 둔다.
5. 비활성화 또는 소속 해제 대상 사용자가 active sales claim을 보유하면 409로 차단한다.
6. 먼저 영업을 이관하거나 해제해야 한다.

삭제 정책:

1. 운영 기본은 삭제보다 비활성화/소속 해제다.
2. 현행 호환상 관리자는 사용자 삭제 API를 사용할 수 있다.
3. 삭제는 Supabase auth user와 관련 profile/membership/invitation/audit/run preset/pipeline/tracker audit/sales claim 데이터를 실제 삭제할 수 있다.
4. 새 제품에서 법적/운영상 감사 보존이 중요하면 hard delete는 platform admin 전용 비상 기능으로 축소해야 한다.

## 6. 화면 구조

### 6.1 전체 shell

로그인 후 화면은 아래 영역으로 구성한다.

1. 상단 header/meta
2. 사용자/관리자 모드 전환
3. 사용자 모드 홈
4. 관리자 콘솔 영역
5. 실행 생성
6. 실행 상세
7. 최근 실행
8. 로그
9. 리포트
10. 아티팩트
11. 트래커 보드/목록
12. 영업 패널
13. 조직 관리
14. Google Sheets 관리자 탭
15. 진단 패널

사용자 모드에서는 업무에 필요한 최소 영역만 노출한다. 관리자 모드에서는 운영/검증/진단 영역을 추가 노출한다.

### 6.2 사용자 모드

사용자 모드의 핵심 화면은 영업 홈이다.

영역은 아래 3개다.

1. `내가 진행 중인 영업`
2. `회사 전체 진행 중인 영업`
3. `전체 영업 대상 프로젝트`

`내가 진행 중인 영업` 카드 표시 필드:

1. 프로젝트명
2. 발주처/수요기관
3. 연면적
4. 공사비
5. 빌딩자동제어 추정금액
6. 설계사무소
7. 개찰예정일
8. 착공/완공 관련 일정
9. 담당자
10. 현장
11. 영업 시작일
12. 현재 담당 시작일
13. 현재 상태 badge
14. 영업현황 메모 history
15. 새 메모 textarea
16. 이관 대상 선택

사용자 액션:

1. 메모 저장
2. 계약 완료
3. 영업 종료
4. 해제
5. 이관
6. 엑셀 다운로드
7. 연관 공고 열기
8. 공고문 보기

메모는 append-only를 기본으로 한다. Ctrl/Cmd+Enter 저장을 지원한다. 계약 완료는 계약금액 입력 modal을 열고, 금액이 없으면 저장하지 않는다.

`회사 전체 진행 중인 영업`은 읽기 전용이다. owner 이름/이메일, 최근 메모, 상태를 볼 수 있지만 수정/이관/종료/해제 버튼은 없다.

`전체 영업 대상 프로젝트`는 아직 active claim이 없는 tracker entry만 보여주는 것이 목표다. 현재 구현은 tracker summary 전체를 받은 뒤 sales claim 정보를 결합해 버튼/상태를 조정한다. 재구축에서는 가능하면 API 또는 read model에서 `unclaimed_only`에 준하는 필터를 제공하는 것이 좋다.

### 6.3 관리자 모드

관리자 모드에서는 아래 패널을 노출한다.

1. 운영 대시보드
2. 실행 생성/최근 실행/실행 상세
3. 로그 패널
4. 최신 리포트/리포트 job
5. 아티팩트/preview/download
6. 트래커 보드와 inline editor
7. tracker 상세 drawer
8. 관리자 영업 집계
9. 종료/완료 정리
10. 조직 사용자/초대 관리
11. 감사 로그
12. Google Sheets 관리자 화면
13. tracker 진단/cleanup/backfill/contact resolution

관리자 모드는 실시간 자동 polling을 무조건 사용하지 않는다. 영업 집계는 액션 발생 또는 수동 새로고침 시 갱신한다. 실행/로그/tracker export는 진행 중일 때 polling 또는 SSE를 사용할 수 있다.

### 6.4 관리자 상단 탭과 legacy route

관리자 화면은 상단 탭을 가질 수 있다.

필수 탭:

1. 프로젝트 현황
2. Google Sheets 시트 탭들

legacy route alias는 현재 구현 호환을 위해 지원할 수 있다.

예:

1. `/app/design-list`
2. `/app/planned-orders`
3. `/app/lost`
4. `/app/agency-list`

위 alias는 새 라우터에서 같은 앱 shell로 연결하되, 실제 탭/필터 상태만 다르게 초기화한다.

## 7. 실행, 리포트, 아티팩트

### 7.1 실행 생성

실행 생성은 `POST /api/runs`로 `project_tracker` run을 만든다.

입력 필드:

1. 시작일
2. 종료일
3. 계약일 힌트
4. 공고번호
5. 공고명
6. 수요기관
7. 페이지당 행 수
8. 최대 페이지 수
9. API 범위
10. 고급 옵션

검증:

1. 공고번호, 공고명, 수요기관 중 하나 이상은 필수다.
2. 날짜는 `YYYYMMDD` 기준으로 정규화한다.
3. API 범위는 `construction`, `service`, `goods`, `all` 중 하나다.

고급 옵션:

1. `collect_mode`: `auto`, `native`, `synthetic`
2. stage delay
3. LLM correction 사용 여부
4. LLM model
5. LLM 최대 처리 수
6. export parallel worker

### 7.2 run lifecycle

상태값:

1. `queued`
2. `running`
3. `success`
4. `failed`
5. `cancelled`

`project_tracker` 단계:

1. `collect`
2. `filter`
3. `rescan`
4. `export`
5. `finalize`

`tracker_export` 단계:

1. `tracker_export`
2. `finalize`

`POST /api/runs`는 run row를 `queued`로 만들고 background 실행을 시작한다.

취소는 즉시 `cancelled`로 바꾸지 않고 `cancel_requested=true`를 먼저 기록한다. worker는 stage 경계에서 취소 요청을 확인하고 `cancelled`로 전환한다. 이미 `success`, `failed`, `cancelled`인 run에는 cancel 요청이 409로 실패한다.

### 7.3 tracker export

`project_tracker` 성공 후 자동으로 child `tracker_export`를 queue한다.

수동 export endpoint:

`POST /api/runs/{run_id}/tracker-export`

규칙:

1. parent run은 존재해야 한다.
2. parent run은 operational view에서 visible해야 한다.
3. parent run이 성공 상태여야 한다.
4. 같은 parent의 child `tracker_export`가 `queued`, `running`, `success`면 재사용한다.
5. 실패한 child가 있으면 새 child를 만들 수 있다.
6. 자동 export와 수동 export는 같은 queue helper를 사용한다.

### 7.4 SSE와 자동 갱신

SSE endpoint:

`GET /api/runs/{run_id}/events`

요구사항:

1. `text/event-stream`으로 응답한다.
2. `run`, `log`, `error`, `complete` 이벤트를 제공한다.
3. poll interval query는 250ms 이상 10,000ms 이하로 제한한다.
4. run이 terminal 상태가 되면 complete 이벤트를 보낸다.
5. SSE가 실패하면 클라이언트는 일반 polling으로 degrade할 수 있다.

### 7.5 실행 목록과 상세

실행 목록 필터:

1. 상태
2. run type
3. parent run id
4. from/to 날짜
5. page
6. page_size

실행 상세 표시:

1. run id
2. 상태 badge
3. 진행률
4. run type
5. progress stage
6. params JSON
7. summary JSON
8. error JSON
9. parent/child 연결 정보
10. created/started/finished timestamps
11. tracker export 진행 카드
12. workbook preview

### 7.6 리포트 job

리포트 패널은 아래를 지원한다.

1. report name 선택
2. seed limit 입력
3. report job 생성
4. 최근 report job 조회
5. job 상세 조회
6. report JSON 조회
7. summary/raw JSON 표시

현재 구현은 report job을 memory queue로 관리하고 결과 JSON 파일을 읽는다. 재구축에서 95% 호환을 목표로 하면 memory queue도 허용한다. 장기 운영 제품으로 만들려면 DB job table을 후속 과제로 둔다.

### 7.7 아티팩트

아티팩트는 DB metadata와 local file storage로 분리한다.

DB metadata:

1. artifact id
2. run id
3. artifact type
4. file name
5. storage path
6. content type
7. size
8. created_at

파일 본문은 local filesystem에서 읽어 `FileResponse`로 다운로드한다.

아티팩트 UI는 아래 섹션으로 묶는다.

1. 선택 run artifacts
2. parent project_tracker artifacts
3. child tracker_export artifacts

정렬 우선순위:

1. `execution_manifest`
2. CSV 계열
3. `tracking_excel`
4. 기타

preview 가능 artifact는 preview 토글을 제공한다. CSV와 `tracking_excel`은 인콘솔 preview를 지원한다. tracking workbook artifact가 늦게 생성되는 경우 child run 조회 후 retry한다.

## 8. 트래커

### 8.1 트래커 API

주요 endpoint:

| 기능 | Method | Path |
| --- | --- | --- |
| 홈 bootstrap | GET | `/api/home-bootstrap` |
| 트래커 summary 목록 | GET | `/api/tracker-entry-summaries` |
| 트래커 상세 목록 | GET | `/api/tracker-entries` |
| summary 다운로드 | GET | `/api/tracker-entry-summaries/download` |
| 비동기 다운로드 job 생성 | POST | `/api/tracker-entry-summaries/download-jobs` |
| 다운로드 job 조회 | GET | `/api/tracker-entry-summaries/download-jobs/{job_id}` |
| 다운로드 job 파일 | GET | `/api/tracker-entry-summaries/download-jobs/{job_id}/file` |
| 다운로드 warm | POST | `/api/tracker-entry-summaries/download/warm` |
| template 상태 | GET | `/api/tracker-template` |
| template 업로드 | POST | `/api/tracker-template` |
| template override 삭제 | DELETE | `/api/tracker-template` |
| missing report | GET | `/api/tracker-entries/missing-report` |
| missing report 다운로드 | GET | `/api/tracker-entries/missing-report/download` |
| entry 수정 | PATCH | `/api/tracker-entries/{entry_id}` |
| entry 상세 | GET | `/api/tracker-entries/{entry_id}` |
| 공고문 파일 보기 | GET | `/api/tracker-entries/{entry_id}/notice-file-view` |
| entry 감사 로그 | GET | `/api/tracker-entries/{entry_id}/audit-logs` |
| 변경 이벤트 unread | GET | `/api/tracker-change-events/unread-count` |
| 변경 이벤트 목록 | GET | `/api/tracker-change-events` |
| 변경 이벤트 읽음 처리 | POST | `/api/tracker-change-events/mark-read` |

### 8.2 트래커 데이터 모델

트래커는 source 값과 override 값을 분리한다.

필수 구조:

1. `tracker_entries`: source/override 컬럼 보유
2. `tracker_entries_effective`: effective view
3. `tracker_entry_audit_logs`: field override 감사 로그
4. `tracker_change_events`: 변경 알림 이벤트
5. `tracker_entry_snapshots`: 홈/목록 최적화 snapshot
6. `backfill_conflicts`: 안전 백필 충돌 검토

`tracker_entries.project_id`는 현재 구현 기준 저장 컬럼이 아니다. API read model 또는 project aggregate 과정에서 파생될 수 있다.

### 8.3 editable field와 override

웹에서 수정 가능한 field는 repository의 editable field 목록으로 제한한다.

수정 API 요청:

1. `field_name`
2. `value`
3. `actor_user_id`
4. `actor_label`
5. `change_source`

수정 결과:

1. `changed`
2. 최신 entry
3. audit log
4. 변경 이벤트

source-only presentation 필드는 override하지 않는다. 예: 일정 split 계열 source-only 필드.

### 8.4 트래커 보드

관리자 모드의 보드는 table이다.

필수 동작:

1. column header 정렬
2. 빈 값 우선 정렬
3. 지역/시트/섹션/검색/edited only 필터
4. 페이지 이동
5. cell inline edit
6. Enter 저장
7. Esc 취소
8. textarea Shift+Enter 줄바꿈
9. override 상태 표시
10. source/evidence 표시
11. save success 후 해당 row와 detail cache 갱신

### 8.5 사용자 모드 프로젝트 카드

사용자 모드의 영업 대상 프로젝트 카드는 tracker summary를 기반으로 렌더한다.

표시 필드:

1. No
2. 프로젝트명
3. 발주처/수요기관
4. 연면적
5. 공사비
6. 빌딩자동제어 추정금액
7. 설계사무소
8. 개찰예정일
9. 착공 또는 일정 힌트
10. 담당/연락처
11. 현장/지역
12. 상태 badge

액션:

1. 영업 시작
2. 연관 공고 열기
3. 공고문 보기
4. 엑셀 다운로드

진행 중/종료/완료된 프로젝트는 신규 영업 대상에서 숨기는 것이 목표다. 현재 구현이 클라이언트 결합으로 처리하는 부분은 재구축 시 API 필터로 강화할 수 있다.

### 8.6 missing report

missing report는 tracker entry의 핵심 필드 누락을 진단한다.

지원:

1. 요약 통계
2. 누락 entry 목록
3. 누락 field key/label
4. source reason
5. CSV 다운로드
6. XLSX 다운로드

관리자 진단 패널과 다운로드 버튼에서 접근한다.

### 8.7 tracker change events

이벤트 type:

1. `related_notice_added`
2. `field_filled`
3. `field_updated_safe`
4. `field_conflict_detected`
5. `manual_updated`

요구사항:

1. `dedupe_key`로 중복 삽입을 방지한다.
2. unread count를 제공한다.
3. 목록 조회는 limit와 entry filter를 지원한다.
4. mark-read는 전체 또는 지정 id들을 읽음 처리한다.
5. change bell UI는 unread count와 recent changes를 보여준다.

### 8.8 backfill conflict와 cleanup

backfill conflict는 관리자 전용이다.

지원:

1. conflict 목록 조회
2. field별 current/candidate/source 표시
3. resolution 선택
4. resolve 저장

resolution:

1. `kept_current`
2. `applied_manually`
3. `applied_via_backfill`
4. `dismissed`

현재 resolve API는 resolution을 기록할 뿐 tracker value를 자동 patch하지 않는다.

cleanup은 관리자 전용 운영 도구다.

지원:

1. source tracker run scope 선택
2. cleanup preview
3. 삭제/정리 대상 count 표시
4. apply
5. apply 불가 사유 표시

cleanup은 운영 위험이 있으므로 preview 없이 apply할 수 없어야 한다.

### 8.9 contact resolution summary

연락처 재추출 검증은 관리자 진단 기능이다.

요구사항:

1. source tracker run 기준 summary 조회
2. winner CSV 또는 tracker entry 기반 매칭
3. `demand_contact_resolution_*` 필드 집계
4. status/reason/phase/role/owner side/basis 표시
5. 누락/충돌/개선 후보 구분

## 9. 관련 공고

### 9.1 관련 공고 API

주요 endpoint:

1. `GET /api/projects`
2. `GET /api/projects/{project_id}/related-notices`
3. `GET /api/projects/{project_id}/notice-view`
4. `GET /api/notices/view`

### 9.2 read path

관련 공고 조회는 아래 순서로 처리한다.

1. response memory cache 확인
2. published snapshot/global cache 확인
3. precompute state 확인
4. precompute queue 요청
5. pending/missing 응답 반환

live search는 현재 주요 read path가 아니며 precompute 중심이다.

### 9.3 DB 모델

필수 테이블:

1. `project_related_notice_cache`
2. `related_notice_publications`

`project_related_notice_cache`는 `organization_id`, `snapshot_set_id`, `project_key` 조합으로 cache를 관리한다.

`related_notice_publications`는 조직별 현재 published snapshot pointer 역할을 한다.

### 9.4 UI

프로젝트 카드의 `연관 공고 열기` 버튼은 panel을 토글한다.

상태별 표시:

1. 로딩
2. 준비 중
3. 저장본 없음
4. 같이 수집된 공고 없음
5. 준비 실패
6. 조회 실패
7. 완료

ready payload는 localStorage에 TTL cache할 수 있다. pending 또는 seed fallback 상태에서는 panel이 열려 있는 동안 후속 refresh를 예약한다.

각 항목은 프로젝트명, 공고번호, 차수, 공고일, 수요기관, 공고문 열기 버튼을 포함한다.

공고문 보기는 새 창에서 렌더한다. 팝업 차단, URL 없음, viewer 로드 실패는 사용자에게 명확히 표시한다.

## 10. 영업 파이프라인

### 10.1 Sales API

표준 endpoint:

| 기능 | Method | Path |
| --- | --- | --- |
| claim 목록 | GET | `/api/sales-claims` |
| 사용자 홈 overview | GET | `/api/sales-claims/overview` |
| 엑셀 다운로드 | GET | `/api/sales-claims/export` |
| 영업 시작 | POST | `/api/sales-claims/projects/{project_id}/claim` |
| 메모 수정 | PATCH | `/api/sales-claims/projects/{project_id}` |
| 이관 | POST | `/api/sales-claims/projects/{project_id}/transfer` |
| 종료 | POST | `/api/sales-claims/projects/{project_id}/close` |
| 해제 | POST | `/api/sales-claims/projects/{project_id}/release` |
| 사용자별 집계 | GET | `/api/sales-claims/summary-by-user` |

### 10.2 Sales DB 모델

필수 테이블:

1. `project_sales_claims`
2. `project_sales_claim_events`

active claim lock는 `(organization_id, project_id)` 기준이다.

이벤트 type:

1. `claim`
2. `note_update`
3. `transfer`
4. `release`
5. `force_release`
6. `close_won`
7. `close_lost`

현재 구현 기준 이벤트 actor는 `actor_user_id`, `actor_email`, `actor_display_name` 중심이다. `actor_membership_id`는 필수 표준으로 보지 않는다.

### 10.3 영업 시작

영업 시작 조건:

1. 로그인 사용자가 active membership을 가져야 한다.
2. 같은 조직/프로젝트의 active claim이 없어야 한다.
3. 같은 사용자가 이미 claim한 경우 `changed=false`를 반환할 수 있다.
4. 다른 사용자가 active claim 중이면 409 conflict다.

claim 생성 시 저장:

1. project id
2. source entry id
3. source run id
4. project name
5. estimated amount text
6. owner user id
7. owner email
8. owner display name
9. sales note
10. claimed_at
11. current_owner_assigned_at

### 10.4 메모

메모 수정은 기본적으로 owner만 가능하다.

관리자는 `force_admin_override=true`로 강제 수정할 수 있다. 현재 UI의 최근 메모 삭제는 별도 delete API가 아니라 마지막 메모 줄을 제거한 전체 `sales_note`를 PATCH하는 방식이다.

메모 정책:

1. 일반 사용자에게 delete 버튼을 제공하지 않는다.
2. 정정은 새 메모 append를 기본으로 한다.
3. 관리자 최근 메모 삭제는 운영 예외로 허용한다.
4. 삭제성 수정은 감사 또는 sales event로 추적해야 한다.

### 10.5 이관

이관은 owner 또는 관리자 force만 가능하다.

조건:

1. target user가 있어야 한다.
2. 같은 대상자로 이관할 수 없다.
3. closed claim은 이관할 수 없다.
4. 관리자는 force 이관 가능하다.

이관 시:

1. owner 정보를 새 사용자로 변경한다.
2. `current_owner_assigned_at`을 갱신한다.
3. 시스템 메모를 append한다.
4. `transfer` event를 기록한다.

현재 구현은 "이관 요청 후 승인"이 아니라 직접 이관이다.

### 10.6 종료와 해제

종료는 `won` 또는 `lost`다.

`won`:

1. 계약 완료를 의미한다.
2. 계약금액 입력이 필수다.
3. `claim_status=won`이 된다.
4. `close_won` event를 남긴다.

`lost`:

1. 영업 종료/실패/중단을 의미한다.
2. 계약금액은 요구하지 않는다.
3. `claim_status=lost`가 된다.
4. `close_lost` event를 남긴다.

종료 후 일반 수정/이관/재종료는 차단한다.

해제는 결과 상태가 아니라 담당 잠금 해제다.

해제 시:

1. `is_active=false`
2. `released_at` 기록
3. `release` 또는 `force_release` event 기록
4. 신규 영업 대상 목록에 다시 노출될 수 있음

### 10.7 관리자 집계와 archive

관리자 영업 패널은 아래를 제공한다.

1. 사용자별 active count
2. 총 추정금액
3. 진행 프로젝트 목록
4. elapsed days
5. owner elapsed days
6. 최신 메모 요약
7. 강제 해제
8. 최근 메모 삭제

종료/완료 정리는 아래를 제공한다.

1. 연도 그룹
2. 월 그룹
3. 계약 완료 section
4. 영업 종료 section
5. 계약금액 또는 추정금액

미래 연도는 노출하지 않는다.

## 11. 조직 운영과 감사

### 11.1 조직 운영 bootstrap

관리자 패널은 `/api/admin/organization-panel-bootstrap`으로 초기 데이터를 묶어 받을 수 있다.

포함:

1. members
2. plan summary
3. pending invitations
4. auth audit logs slice
5. download audit logs slice
6. login audit logs slice
7. generated_at

각 log slice는 기본 5개와 `has_more`를 포함한다.

### 11.2 platform admin 계정 도구

`platform_admin`만 아래를 수행한다.

1. `/api/admin/accounts`로 계정 직접 생성
2. `/api/admin/accounts/{user_id}/password-reset`으로 비밀번호 관리자 초기화

직접 생성 입력:

1. 이메일
2. 표시 이름
3. 역할
4. 초기 비밀번호

비밀번호 재설정 제한:

1. bootstrap platform admin 계정 금지
2. 자기 계정 금지
3. platform admin만 허용

### 11.3 감사 로그

인증/조직 감사 로그는 `audit_logs`에 저장한다.

필수 이벤트:

1. `invite_created`
2. `invite_accepted`
3. `invite_revoked`
4. `membership_role_changed`
5. `membership_deactivated`
6. `membership_reactivated`
7. `account_created`
8. `account_password_reset`
9. `project_transferred`

로그인 로그는 별도 `login_audit_logs`에 저장한다. 현재 구현 기준 성공한 authorized login만 필수 기록이다.

다운로드 로그는 별도 `download_audit_logs`에 저장한다. 영업/트래커 다운로드의 scope, format, source_page, file_name을 기록한다.

## 12. Google Sheets 관리자

### 12.1 목적

Google Sheets 관리자 화면은 운영자가 외부 Google Sheets 데이터를 읽기 전용으로 빠르게 확인하고, 수동 동기화하고, 시트별 필터/정렬을 적용하는 기능이다.

### 12.2 API

| 기능 | Method | Path |
| --- | --- | --- |
| bootstrap | GET | `/api/admin/google-sheets/bootstrap` |
| sheet payload | GET | `/api/admin/google-sheets/sheets/{sheet_key}` |
| sync trigger | POST | `/api/admin/google-sheets/sync` |

모든 API는 관리자만 호출할 수 있다.

### 12.3 bootstrap 응답

포함:

1. enabled
2. source_title
3. source_url
4. sync_status
5. last_successful_sync_at
6. last_failed_sync_at
7. last_error
8. tabs

Google Sheets 설정이 없으면 `enabled=false`, `sync_status=not_configured`, 빈 tabs를 반환한다.

### 12.4 UI

상단 admin nav는 기본 프로젝트 현황 탭과 Google Sheets tabs를 표시한다.

시트 탭 표시:

1. status badge
2. source title/url
3. sync timestamp
4. active sheet label
5. 동기화 버튼
6. read-only table
7. column filter popup
8. search
9. value checkbox
10. asc/desc sort

동기화 버튼을 누르면 `/api/admin/google-sheets/sync`를 호출한다. `queued` 또는 `already_running`이면 1.5s, 3s, 6s, 10s, 15s 순서로 follow-up refresh한다.

안전한 http/https link cell은 새 탭 링크로 렌더한다.

필터 결과가 없으면 "조건에 맞는 데이터가 없습니다."를 표시한다.

## 13. Report, Preset, Home Bootstrap, Download Job

### 13.1 run preset

run preset은 최근 실행 조건을 저장/적용하는 기능이다.

API:

1. `GET /api/run-presets`
2. `POST /api/run-presets`

현재 구현은 memory store 최근 50개 기준이다. 재시작 시 소실될 수 있다.

### 13.2 tracker download job

비동기 다운로드 job은 큰 tracker workbook 생성 중 UI blocking을 피하기 위한 기능이다.

동작:

1. job 생성 요청
2. filter 기반 cache key 생성
3. 같은 cache key의 queued/running/success job이 있으면 재사용
4. background에서 XLSX 생성
5. job 상태 polling
6. 완료 후 file endpoint로 다운로드

job 파일은 local `.tmp-tracker-download-jobs/{job_id}.xlsx` 계열 경로에 저장한다.

### 13.3 home bootstrap

home bootstrap은 사용자 홈 초기 표시 속도를 위한 통합 read model이다.

포함:

1. sales overview
2. tracker 첫 페이지
3. generated_at
4. sort contract

Supabase snapshot이 fresh하면 그대로 반환하고, 아니면 재생성해 best-effort upsert한다.

정렬 기준:

1. `opening_scheduled_date_desc`
2. `updated_at_desc`
3. `id_desc`

## 14. 데이터 저장소와 배포/환경

### 14.1 repository backend

repository backend는 도메인별로 `in_memory`, `supabase`, `auto`를 지원한다.

기본 선택:

1. `SUPABASE_URL`과 backend key가 있으면 `supabase`
2. 없으면 `in_memory`
3. 도메인별 env가 있으면 해당 값을 우선

주요 env:

1. `TRACKER_REPOSITORY_BACKEND`
2. `RUN_REPOSITORY_BACKEND`
3. `ARTIFACT_REPOSITORY_BACKEND`
4. `RUN_LOG_REPOSITORY_BACKEND`
5. `SALES_CLAIM_REPOSITORY_BACKEND`
6. `RELATED_NOTICE_*`
7. `DOWNLOAD_AUDIT_LOG_*`
8. `LOGIN_AUDIT_LOG_*`
9. `HOME_BOOTSTRAP_*`
10. `BACKFILL_CONFLICT_*`

### 14.2 Supabase 핵심 테이블

Core:

1. `organizations`
2. `users`
3. `pipeline_runs`
4. `pipeline_logs`
5. `run_artifacts`
6. `saved_run_presets`

Auth/Org:

1. `user_profiles`
2. `organization_memberships`
3. `invitations`
4. `audit_logs`
5. `login_audit_logs`
6. `download_audit_logs`

Tracker:

1. `tracker_entries`
2. `tracker_entries_effective`
3. `tracker_entry_audit_logs`
4. `tracker_change_events`
5. `backfill_conflicts`
6. `tracker_entry_snapshots`

Sales:

1. `project_sales_claims`
2. `project_sales_claim_events`

Related Notice:

1. `project_related_notice_cache`
2. `related_notice_publications`

Home:

1. `home_bootstrap_snapshots`

### 14.3 legacy users

현재 구현은 `user_profiles`/`organization_memberships`를 사용하면서도 legacy `users` table projection과 fallback을 유지한다.

재구축 기준:

1. 새 제품에서는 `user_profiles`와 `organization_memberships`를 권한 기준으로 삼는다.
2. 기존 데이터 호환이 필요하면 `users` projection bridge를 둔다.
3. pipeline/tracker/sales FK가 legacy users를 참조하는 경우 migration bridge를 명시한다.
4. 신규 설계에서 단순 `users.organization_id`만으로 조직 권한을 판단하지 않는다.

## 15. 외부 수집, native/synthetic mode, 진단

### 15.1 collect mode

`advanced_options.collect_mode`는 아래 값을 가진다.

1. `auto`
2. `native`
3. `synthetic`

`auto`는 native API/web stage를 우선 시도한다. synthetic debug fallback은 명시적으로 허용된 경우에만 가능하다.

`synthetic`은 debug-only 모드이며 `PROJECT_TRACKER_ENABLE_SYNTHETIC_DEBUG=1`이 필요하다.

### 15.2 native pipeline

native pipeline은 아래 단계와 서비스로 구성된다.

1. seed collect
2. native filter
3. native rescan
4. native export
5. tracker materialization
6. related notice precompute
7. contact resolution
8. artifact generation

외부 소스는 나라장터/G2B, LOFIN, EAIS, HUB 등으로 확장되어 있다. 재구축 명세에서는 특정 기관 API key나 내부 운영 값을 포함하지 않고, provider abstraction과 fallback/timeout/diagnostic policy만 명시한다.

### 15.3 진단 필드

tracker/contact/native 진단은 summary와 관리자 패널에서 표시할 수 있어야 한다.

예:

1. source path
2. extraction status
3. resolution reason
4. contact role
5. owner side
6. lookup provider
7. timeout/fallback 여부
8. missing reason

## 16. 오류, 빈 상태, 수용 기준

### 16.1 공통 오류 규칙

API 오류는 아래 shape를 따른다.

1. `code`
2. `message`
3. optional details

UI는 기술 오류를 그대로 노출하지 않고 사용자 행동 기준 문구로 정규화한다.

예:

1. 로그인 실패: 이메일 또는 비밀번호 오류
2. 권한 없음: 관리자만 사용할 수 있음
3. 초대 만료: 새 초대를 요청
4. active sales claim 충돌: 이미 다른 사용자가 진행 중
5. 사용자 비활성화 실패: 진행 중 영업 이관/해제 필요

### 16.2 빈 상태

빈 상태는 영역별로 구분한다.

1. 최근 실행 없음
2. 선택 run 없음
3. 로그 없음
4. artifact 없음
5. 내 영업 없음
6. 회사 진행 영업 없음
7. 신규 영업 대상 없음
8. pending 초대 없음
9. Google Sheets 설정 없음
10. Google Sheets 조건 일치 행 없음
11. 관련 공고 준비 중/없음/실패
12. tracker missing report 없음
13. backfill conflict 없음

### 16.3 인수 기준

새 구현이 현재 시스템과 95% 이상 유사하다고 보려면 아래를 충족해야 한다.

1. `/api/auth/sign-in/sign-up/sign-out/session/import/password-reset` 흐름이 현재 UI와 호환된다.
2. 역할별 UI 노출과 서버 403/409 권한 검사가 일치한다.
3. 초대 생성/preview/accept/revoke, plan limit, fallback link 흐름이 동작한다.
4. 사용자 모드 3영역 영업 홈이 동일한 정보 구조와 액션을 제공한다.
5. 관리자 모드에서 실행/로그/리포트/아티팩트/트래커/영업/조직/진단을 사용할 수 있다.
6. `POST /api/runs` 후 run lifecycle과 자동 tracker export가 동작한다.
7. `POST /api/runs/{run_id}/tracker-export`는 기존 child 재사용 정책을 따른다.
8. tracker board inline edit와 audit/change event가 동작한다.
9. related notice는 published snapshot/cache/pending 상태를 구분한다.
10. sales claim은 claim/update/transfer/close/release와 event 기록을 현재와 동일하게 처리한다.
11. Google Sheets 관리자 화면이 설정 없음/동기화 중/성공/실패 상태를 표시한다.
12. artifact download/preview는 local file storage + DB metadata 방식으로 동작한다.
13. login/download/auth audit log가 관리자 화면에서 조회된다.
14. hard delete API는 현행 호환 또는 명시적 제외 중 하나로 결정되어 문서/구현이 일치한다.

## 17. 기존 정본 문서 반영 계획

이 문서를 검토한 뒤 기존 정본 문서는 아래 순서로 갱신한다.

1. `FUNCTIONAL_SPEC_KR.md`
   - Google Sheets, 진단, platform admin tools, related notice snapshot, download jobs, run presets 추가
   - 영업 대상 포함/제외 조건 정리
   - 직접 이관/직접 종료 정책 명시
2. `UI_SCREEN_SPEC_KR.md`
   - 관리자 상단 탭, Google Sheets, 진단 패널, tracker drawer, home bootstrap 기반 사용자 홈 상세화
3. `TECHNICAL_SPEC_KR.md`
   - endpoint 경로 정정
   - tracker export 재사용 정책
   - artifact local storage 계약
   - sales event type 정리
4. `SYSTEM_DESIGN_KR.md`
   - related notice publication/cache
   - memory store와 DB store 경계
   - legacy users bridge
5. `OPERATIONS_POLICY_KR.md`
   - hard delete 예외
   - 메일 fallback
   - 감사 로그 scope
   - platform admin 현재 조직 범위
6. `REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md`
   - 실제 구현 순서에 Google Sheets/진단/download job/home bootstrap/report jobs 추가

## 18. 참고한 주요 구현 파일

Backend:

1. `backend/api/app.py`
2. `backend/api/routers/registration.py`
3. `backend/api/routers/auth.py`
4. `backend/api/routers/admin.py`
5. `backend/api/routers/runs.py`
6. `backend/api/routers/tracker.py`
7. `backend/api/routers/tracker_admin.py`
8. `backend/api/routers/backfill_conflicts.py`
9. `backend/api/routers/sales_claims.py`
10. `backend/api/routers/related_notice.py`
11. `backend/api/routers/reports.py`
12. `backend/api/routers/artifacts.py`
13. `backend/repositories/factory.py`
14. `backend/repositories/supabase_tracker_entries.py`
15. `backend/repositories/supabase_sales_claims.py`
16. `backend/services/run_execution_project_tracker.py`
17. `backend/services/run_execution_tracker_export.py`
18. `backend/services/run_execution_tracker_queue_runtime.py`
19. `backend/services/google_sheets_admin_backend.py`
20. `backend/services/google_sheets_admin_store.py`
21. `backend/services/related_notice_response_backend.py`
22. `backend/services/related_notice_publish_backend.py`
23. `backend/services/tracker_contact_resolution_backend.py`
24. `backend/services/home_bootstrap_backend.py`
25. `backend/services/tracker_download_job_store.py`

Frontend:

1. `frontend/index.html`
2. `frontend/auth-controller.js`
3. `frontend/auth-session-runtime.js`
4. `frontend/auth-ui-controller.js`
5. `frontend/ui-mode-controller.js`
6. `frontend/run-panels-controller.js`
7. `frontend/run-view-runtime.js`
8. `frontend/artifact-runtime.js`
9. `frontend/report-panels-controller.js`
10. `frontend/tracker-controller-entries-runtime.js`
11. `frontend/tracker-board-runtime.js`
12. `frontend/selected-entry-runtime.js`
13. `frontend/project-related-controller.js`
14. `frontend/related-notice-runtime.js`
15. `frontend/sales-view-runtime.js`
16. `frontend/sales-panel-controller-actions.js`
17. `frontend/sales-panel-controller-markup.js`
18. `frontend/organization-admin-runtime.js`
19. `frontend/org-admin-runtime.js`
20. `frontend/platform-admin-account-runtime.js`
21. `frontend/admin-google-sheets-controller.js`
22. `frontend/admin-google-sheets-runtime.js`
23. `frontend/app-admin-google-sheets-runtime.js`
24. `frontend/tracker-diagnostics-runtime.js`
25. `frontend/tracker-diagnostics-panel-controller.js`

Supabase:

1. `supabase/migrations/202603120001_phase1_core_schema.sql`
2. `supabase/migrations/202603120002_tracker_entries_editable.sql`
3. `supabase/migrations/202603120003_apply_tracker_entry_override_rpc.sql`
4. `supabase/migrations/202603160001_project_related_notice_cache.sql`
5. `supabase/migrations/202603200001_project_sales_claims.sql`
6. `supabase/migrations/202603210001_sales_claim_lifecycle_and_user_status.sql`
7. `supabase/migrations/202603210002_phase2_auth_profiles_memberships.sql`
8. `supabase/migrations/202603240003_phase2_auth_plan_limits.sql`
9. `supabase/migrations/202603260002_tracker_change_events.sql`
10. `supabase/migrations/202603260003_backfill_conflicts.sql`
11. `supabase/migrations/202603280001_tracker_entry_snapshots.sql`
12. `supabase/migrations/202603290001_home_bootstrap_snapshots.sql`
13. `supabase/migrations/202603310001_download_audit_logs.sql`
14. `supabase/migrations/202604010001_login_audit_logs.sql`
15. `supabase/migrations/202604010002_platform_admin_account_creation.sql`
16. `supabase/migrations/202604080001_related_notice_publications.sql`

