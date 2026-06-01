# Phase 2 인증 및 B2B 운영 명세

## 연관 문서
- [PHASE2_PLATFORM_LAYER_ARCHITECTURE_KR.md](./PHASE2_PLATFORM_LAYER_ARCHITECTURE_KR.md)
- [PHASE2_DISCUSSION_AND_CURRENT_DESIGN_HANDOFF_KR.md](./PHASE2_DISCUSSION_AND_CURRENT_DESIGN_HANDOFF_KR.md)
- [PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md](./PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md)

이 문서는 기존 Phase 2의 인증/권한/조직 범위 설계 위에, 실제 B2B SaaS 판매/운영에 필요한 정책을 덧붙여 고정한다.

## 1. 목표

Phase 2의 목표는 단순 로그인 추가가 아니다.

1. 서비스를 회사(`organization`) 단위로 판매한다.
2. 사용자는 개인별 `1인 1계정`으로 로그인한다.
3. 공용 계정 돌려쓰기를 어렵게 만든다.
4. 누가 어떤 run, tracker 수정, 사용자 관리 작업을 했는지 감사 로그로 추적한다.
5. 향후 회사 SSO로 확장 가능한 구조를 유지한다.

## 2. 운영 계층

권장 운영 계층:

1. `platform_admin`
2. `org_admin`
3. `org_member`

정리:

- `platform_admin`
  - 서비스 전체 운영자
  - 회사 생성/비활성화
  - seat 한도 관리
  - 회사 관리자 지정
  - 전체 감사 로그/운영 도구 접근
- `org_admin`
  - 회사 관리자
  - 자기 회사 사용자 초대/비활성화
  - seat 사용량 관리
  - 자기 회사 tracker 수정
  - 자기 회사 run 생성/취소
- `org_member`
  - 일반 실사용자
  - 자기 회사 데이터 조회
  - 정책상 허용 시 run 생성

중요:

- `platform_admin`은 회사 소속 사용자 역할과 분리한다.
- 회사 내부 역할은 기존 `users.role` 집합(`admin | member`)을 유지하고,
  플랫폼 운영자 권한은 별도 테이블 또는 별도 플래그로 관리한다.

### 2.1 권한 매트릭스

| 기능 | `platform_admin` | `org_admin` | `org_member` |
| --- | --- | --- | --- |
| 관리자 페이지 진입 | 가능 | 가능 | 불가 |
| 플랫폼 관리자 페이지 진입 | 가능 | 불가 | 불가 |
| 조직 사용자 목록 조회(`include_inactive=true`) | 가능 | 가능 | 불가 |
| 조직 사용자 초대 | `org_admin`, `org_member` 초대 가능 | `org_member` 초대 가능 | 불가 |
| 조직 사용자 역할/상태 수정 | 가능 | 가능 | 불가 |
| 조직 감사 로그 조회 | 가능 | 가능 | 불가 |
| 트래커/영업 일반 화면 접근 | 가능 | 가능 | 가능 |

추가 규칙:

1. `platform_admin`은 전역 운영 권한을 가진다.
2. `org_admin`은 자기 조직 범위만 관리한다.
3. `org_member`는 관리자 패널과 조직 운영 API에 접근하지 않는다.

## 3. 인증 방식

기본 인증 플랫폼:

- `Supabase Auth`

초기 허용 로그인 수단:

1. Google 로그인
2. 이메일 로그인

원칙:

1. 별도 서버 전용 `POST /auth/login` API를 추가하지 않는다.
2. 프론트 로그인 화면에서 Supabase Auth 흐름을 사용한다.
3. 가입은 자유가입이 아니라 `초대 기반`만 허용한다.

## 4. 초대 기반 가입 정책

초기 가입 정책:

1. 회사 관리자(`org_admin`) 또는 플랫폼 관리자(`platform_admin`)만 초대 가능
2. 초대된 이메일만 가입 가능
3. 초대한 이메일과 실제 로그인에 사용하는 이메일은 동일해야 함
4. 초대에는 역할과 만료 시각을 포함

예:

- `kim@company.com`으로 초대
- 허용:
  - `kim@company.com` 이메일 로그인
  - `kim@company.com` Google 로그인(해당 이메일이 실제 Google 계정일 때)
- 차단:
  - 다른 이메일로의 임의 가입
  - `shared@company.com` 같은 공용 계정의 무단 사용

## 5. 동일 이메일 계정 연결 정책

같은 검증된 이메일이면 로그인 수단이 달라도 동일 사용자로 연결한다.

예:

- `abc@gmail.com`으로 초대
- `abc@gmail.com` 이메일 로그인 가입
- 이후 `abc@gmail.com` Google 로그인
- 내부 사용자 계정은 하나로 유지

정책:

1. 초대 이메일과 동일한 이메일일 때만 계정 연결 허용
2. 동일 이메일의 다른 provider identity는 하나의 사용자에 매핑
3. 초대 이메일과 불일치하면 가입/로그인 완료를 차단

## 6. 사용자 한도 정책

B2B 판매 단위는 회사별 활성 사용자 수와 대기 중 초대 수다.

정책:

1. 정책/계약/API 응답/UI 라벨에서 조직별 현재 적용 한도는 `active_user_limit`, `pending_invite_limit`로 표현한다.
2. `active_user_limit`은 `active account + active membership` 사용자 수 기준이다.
3. `pending_invite_limit`은 `pending invitation` 수 기준이다.
4. `platform_admin`은 기본 active user 계산에서 제외한다.
5. 한도에 도달하면 추가 초대 또는 가입 수락을 차단한다.

예:

- 회사가 `active_user_limit = 20`, `pending_invite_limit = 20` 상태
- 활성 계정은 최대 20개
- pending 초대도 한도에 포함되며, 초과 시 새 초대 발송을 차단
- active 사용자 수가 상한에 도달하면 새 초대/수락을 차단

## 7. 세션 정책

현재 결정:

1. 현재는 `단일 활성 세션(single active session)`을 보장하지 않으며, Phase 2 안정화 범위에서는 이를 구현하지 않는다.
2. 현재 구현은 signed cookie + refresh 기반 세션 유지까지만 포함한다.
3. 계정 공유 억제를 위한 강한 세션 제어는 후속 hardening 단계에서 별도 검토한다.

의미:

1. 현재는 새 로그인 시 기존 세션을 강제 종료하지 않는다.
2. 운영 정책은 계속 `1인 1계정`을 유지하되, 세션 동시성 강제는 다음 단계로 미룬다.
3. 실제 단일 세션이 필요해지면 세션 registry 또는 revoke 리스트 기반 설계가 추가로 필요하다.

비권장:

- MAC 주소 기준 차단
- IP 주소만 기준으로 한 강한 차단

이유:

- 웹 브라우저 환경에서 MAC 주소는 신뢰성 있게 취득/판단하기 어렵다.
- IP 기준 차단은 VPN, LTE, 재택, 사내 NAT 때문에 오탐이 많다.

## 8. 회사 SSO 확장 정책

대형 고객사 대응용 확장 경로:

- Google Workspace
- Microsoft Entra ID
- Okta
- 기타 SAML/OIDC 기반 회사 인증

정책:

1. 초기 Phase 2는 Supabase Auth + 초대 기반으로 시작
2. 이후 상위 고객사에는 `Enterprise SSO` 옵션 제공
3. SSO 도입 후에도 organization, membership, role, audit_log 구조는 유지

의미:

- 회사가 직원 계정을 직접 관리
- 퇴사자/이동자 계정 회수가 쉬움
- 진짜 `1인 1계정` 강제가 가장 자연스럽게 됨

## 9. 감사 로그 정책

반드시 기록할 이벤트:

1. 로그인 성공/실패
2. 로그아웃
3. 초대 발송/수락/만료
4. 사용자 활성화/비활성화
5. 역할 변경
6. run 생성/취소
7. tracker 필드 수정
8. 관리자 설정 변경

감사 로그 공통 필드:

- `organization_id`
- `actor_user_id`
- `actor_label`
- `event_type`
- `target_type`
- `target_id`
- `before_json`
- `after_json`
- `ip`
- `user_agent`
- `created_at`

추가 원칙:

1. 조직 감사 로그 조회는 self-service 운영 추적 범위로 한정한다.
2. 현재 범위는 actor organization 최근 이벤트 조회까지만 포함하며, cross-org 검색, 고급 필터, 내보내기 기능은 후속 운영 고도화 범위로 둔다.

## 10. UI 구조

로그인 전:

1. 로그인 화면
2. 초대 수락 화면
3. 이메일 인증/비밀번호 설정 화면

로그인 후:

1. 공통 상단 바
   - 회사명
   - 사용자명
   - 역할
   - 로그아웃
2. 권한별 패널 분기
   - `platform_admin`: 회사/seat/운영 관리
   - `org_admin`: 사용자/초대/tracker 관리, 조직 감사 로그 조회
   - `org_member`: 회사 데이터 사용

## 11. 권장 출시 순서

### Phase 2A

1. Supabase Auth
2. organization / users / memberships
3. 초대 기반 가입
4. role 분기
5. 감사 로그의 실제 `actor_user_id` 기록

### Phase 2B

1. seat 한도
2. org_admin 사용자 관리 UI
3. 조직 감사 로그 조회 화면
4. 플랫폼 관리자 UI
5. 영업 액션 최소 모델(`owner / priority / next_action / due_date / status / memo`)

### Phase 2C

1. Enterprise SSO
2. 더 세밀한 세션 정책
3. 회사 내부 팀/프로젝트 범위 제어

## 12. 결정 요약

Phase 2 권장 운영안:

1. `Supabase Auth`
2. `Google 로그인 + 이메일 로그인`
3. `초대 기반 가입`
4. `초대 이메일과 동일한 이메일만 허용`
5. `organization` 단위 판매
6. `active_user_limit / pending_invite_limit` 기반 한도 제한
7. `platform_admin > org_admin > org_member`
8. `단일 활성 세션은 Phase 2 안정화 범위에서 보류`
9. 향후 `회사 SSO` 확장
