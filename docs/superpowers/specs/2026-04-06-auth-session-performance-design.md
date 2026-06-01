# Auth Session Performance Design

**Goal**

로그인 및 보호 API 인증 경로에서 반복되는 Supabase 프로필 조회를 줄여, 로그인 타임아웃과 일반 API 지연을 완화한다.

**Scope**

- `backend/api/auth_runtime.py` 의 세션 payload 구성과 auth context 해석
- `frontend/app.js` 의 세션 재확인 호출 빈도 제어
- 관련 auth/unit 테스트 보강

**Out of Scope**

- 운영 서버 배포 및 프로세스 재시작
- EC2 인스턴스 업그레이드
- Supabase 스키마/인덱스 변경

**Current Problem**

- 로그인 시 `sign_in_with_password -> _finalize_session_payload -> _resolve_application_profile -> _get_local_user` 흐름으로 Supabase 프로필 조회가 발생한다.
- 이후 보호 API 요청마다 `read_auth_context()` 가 다시 `_get_local_user()` 를 호출해 `organization_member_profiles` 조회를 반복한다.
- 프론트는 초기 진입, 포커스 복귀, visibility 변경, 401 재시도 시 `/api/auth/session` 을 다시 호출할 수 있다.
- 위 경로가 느려질 때 단일 프로세스 서버와 작은 메모리 환경에서 지연이 증폭된다.

**Design**

- 로그인 시점에는 기존처럼 애플리케이션 프로필을 한 번 조회하고, 결과를 signed session payload 에 충분히 저장한다.
- 일반 보호 API 요청에서는 세션 payload 를 우선 사용해 `AuthContext` 를 구성한다.
- 다만 권한 회수/비활성화 반영이 영구히 늦어지지 않도록, payload 안에 `profile_checked_at` 을 넣고 짧은 TTL 안에서는 무조회, TTL 경과 후에만 `_get_local_user()` 재검증을 수행한다.
- 재검증에 성공하면 최신 role/status/organization 정보를 payload 에 반영할 수 있는 후속 경로를 유지한다.
- 프론트는 `refreshAuthSessionState()` 를 singleflight 로 바꾸고, focus/visibility 기반 재확인은 throttle 한다.

**Key Decisions**

- `read_auth_context()` 는 완전 무조회로 바꾸지 않는다.
  - 이유: 권한 회수, 계정 비활성화, 조직 변경이 세션 만료 시점까지 반영되지 않는 위험이 크다.
- TTL 기반 재검증은 `read_auth_context()` 안에서만 수행한다.
  - 이유: 보호 API 미들웨어 경로를 유지하면서도 DB 조회 빈도를 크게 줄일 수 있다.
- 로그인 성공 응답의 shape 는 유지한다.
  - 이유: 프론트가 로그인 응답의 session payload 를 즉시 사용하고 있다.

**Implementation Notes**

- `backend/api/auth_runtime.py`
  - session payload 에 `profile_checked_at` 추가
  - `read_auth_context()` 에 TTL 재검증 분기 추가
  - `_resolve_application_profile()` 의 `_get_local_user()` 호출은 `auth_user_id` 중심으로 단순화 검토
- `frontend/app.js`
  - `refreshAuthSessionState()` 에 in-flight promise dedupe 추가
  - focus/visibility 이벤트에서 짧은 쿨다운 적용
- 테스트
  - TTL 안에서는 `_get_local_user()` 를 호출하지 않는 케이스
  - TTL 경과 후 inactive 사용자를 차단하는 케이스
  - 프론트 refresh singleflight/throttle 보조 테스트

**Success Criteria**

- 로그인 후 일반 보호 API 다중 호출 시 auth 프로필 조회 횟수가 줄어든다.
- 기존 auth 권한/비활성화 보장 테스트는 유지되거나 더 명확해진다.
- 프론트에서 짧은 시간 내 중복 `/api/auth/session` 호출이 억제된다.
