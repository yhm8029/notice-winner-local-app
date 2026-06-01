# 운영정책 명세서

- 문서 역할: 운영정책 명세서
- 정본 여부: `canonical`
- 이 문서가 답하는 질문: 권한, 초대, 계정 상태, 영업 이관, 삭제 정책, 메일 운영, 감사로그 규칙은 무엇인가
- 이 문서가 답하지 않는 질문: API 필드 상세, DB 컬럼 전체 정의, 화면 배치 세부사항
- 상위 기준 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md), [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md), [SYSTEM_DESIGN_KR.md](./SYSTEM_DESIGN_KR.md)
- 충돌 시 우선 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)

작성일: 2026-03-22  
상태: 통합 초안 v1

## 1. 문서 목적

이 문서는 현재 여러 문서에 흩어져 있는 운영 규칙을 하나의 정책 기준으로 묶는다.

주요 범위:

1. 권한과 역할
2. 초대와 가입
3. 계정/소속 상태
4. 삭제 금지와 비활성화 정책
5. 영업 claim / transfer / close 운영 규칙
6. 감사로그
7. 메일 발송 전략

## 2. 역할 정책

### 2.1 전역 역할

- `platform_admin`

### 2.2 조직 역할

- `org_admin`
- `org_member`

정책:

1. `platform_admin`은 조직 역할에 포함하지 않는다.
2. 권한 판단은 `전역 역할 + membership 역할` 조합으로 해석한다.
3. UI 노출도 위 역할 모델을 따른다.

### 2.3 역할별 행동 매트릭스

`platform_admin`

1. 전역 운영 기능 접근 가능
2. 조직 관리자 계정 bootstrap/점검 가능
3. 모든 관리자 기능 접근 가능
4. `org_admin`, `org_member` 초대 가능
5. `org_admin` 대상 초대의 링크/초기 암호/철회까지 관리 가능

`org_admin`

1. `org_member` 사용자 초대/철회 가능
2. 사용자 역할/소속 상태 변경 가능
3. 영업 강제 해제/강제 이관 가능
4. 종료/완료 정리와 집계 확인 가능
5. `org_member`만 초대 가능
6. `org_admin` 대상 초대는 조회/철회/비밀정보 열람 불가

`org_member`

1. 본인 영업 claim 가능
2. 본인 담당 메모 추가 가능
3. 본인 담당 claim 해제 가능
4. 관리자 영역 접근 불가

## 3. 초대 정책

### 3.1 가입 원칙

1. 공개 자유가입이 아니라 `초대 기반 가입`을 기본으로 한다.
2. 초대 이메일과 실제 로그인 이메일이 일치해야 한다.
3. 초대 수락은 idempotent 해야 한다.
4. 초대 수락은 중복 membership 생성 없이 transaction으로 처리한다.

### 3.2 초대 상태

- `pending`
- `accepted`
- `expired`
- `revoked`

### 3.3 플랜/한도 정책

1. 각 조직은 `plan_code`와 함께 초대/가입 한도를 가진다.
2. 현재 기준 예시는 `플랜 A=5`, `플랜 B=10`, `플랜 C=100`이다.
3. `pending` 초대 수는 초대 한도에 포함한다.
4. `pending` 초대가 한도에 도달하면 철회 또는 만료 전까지 새 초대를 만들 수 없다.
5. `active account + active membership` 사용자 수가 가입 한도에 도달하면 새 초대를 만들 수 없다.
6. 초대 수락 시에도 가입 한도를 다시 확인해야 한다.
7. 관리자 UI는 현재 사용량, 잔여 수량, 업그레이드 필요 여부를 함께 보여준다.

### 3.4 초대 운영 규칙

1. 관리자만 초대를 생성할 수 있다.
2. 철회된 초대는 현재 기준 화면 목록에 계속 노출할 필요는 없다.
3. 초대 이력은 내부 로그에 남길 수 있으나 운영 UI는 `pending` 중심으로 보여준다.
4. 로그인한 본인 이메일을 자기 자신에게 다시 초대하는 동작은 허용하지 않는다.
5. 초대 링크는 메일 자동 발송을 우선하되, 불가 시 링크 직접 전달 fallback을 허용한다.
6. `org_admin`은 자신이 관리 가능한 `org_member` 초대만 목록/철회할 수 있고, `platform_admin`이 만든 `org_admin` 초대의 링크/초기 암호는 노출하지 않는다.

### 3.5 초대 수락 정책

1. 초대 토큰으로 가입/로그인하는 경우에도 초대 이메일과 실제 로그인 이메일이 같아야 한다.
2. 초대 수락은 중복 클릭에도 안전해야 한다.
3. 만료 직전/중복 요청 상황에서도 membership이 중복 생성되면 안 된다.
4. 이미 같은 조직 membership이 존재하면 재생성 대신 연결 또는 수락 처리만 수행한다.
5. 가입 한도 초과 상태라면 수락 단계에서도 차단한다.

### 3.6 초대 메일 운영 정책

1. 초대 메일은 사용자에게 직접 전달되는 실제 onboarding 수단이다.
2. 초대 링크만 생성하고 전달하지 않는 흐름은 임시 fallback일 뿐 기본 운영안이 아니다.
3. 발송 실패 시 관리자에게 명시적으로 알려야 한다.
4. 메일 발송 제한/실패 시 링크 복사로 수동 전달할 수 있어야 한다.

### 3.7 초대 UI 정책

1. 초대 화면은 기본적으로 `pending` 초대만 보여준다.
2. 철회된 초대는 운영 목록에서 숨기고, 필요하면 로그에서만 추적한다.
3. 자기 자신 이메일 초대는 UI와 백엔드 둘 다에서 차단한다.
4. 초대 생성 성공 시 메일 발송 성공/실패와 fallback 여부를 관리자에게 알려야 한다.
5. 플랜 요약 카드에서 `현재 가입 수 / 한도 / 남은 수`, `현재 pending 초대 수 / 한도 / 남은 수`를 보여준다.
6. 한도 초과 시 상위 플랜 업그레이드 안내 문구를 보여준다.
7. 플랜 요약 카드는 서버가 반환한 `plan_summary`를 기준으로 표시한다.

## 4. 계정/소속 상태 정책

### 4.1 `account_status`

- `active`
- `inactive`
- `deactivated`

### 4.2 `membership_status`

- `active`
- `inactive`
- `deactivated`

정책:

1. `account_status`와 `membership_status`는 동일 의미가 아니다.
2. 계정 자체와 조직 내 상태를 분리해서 본다.

### 4.3 상태 의미 고정

`account_status`

1. `active`: 로그인 가능
2. `inactive`: 일시 중지
3. `deactivated`: 사실상 종료

`membership_status`

1. `active`: 해당 회사에서 활동 가능
2. `inactive`: 해당 회사에서 일시 중지
3. `deactivated`: 해당 회사에서 종료/퇴출

### 4.4 상태 전이 허용 규칙

허용:

1. `active -> inactive`
2. `inactive -> active`
3. `active -> deactivated`
4. `inactive -> deactivated`

제한:

1. `deactivated -> active`는 특별 복구 절차 없이는 허용하지 않는다.
2. 진행 중 영업이 남아 있는 membership은 바로 `deactivated`로 가지 않는다.

## 5. 삭제 정책

1. hard delete는 기본 금지다.
2. 계정은 `inactive / deactivated` 중심으로 관리한다.
3. 이력을 깨뜨리는 삭제는 허용하지 않는다.
4. 퇴사/이관 상황은 계정 삭제가 아니라 비활성화 + 이관으로 처리한다.

### 5.1 퇴사자 처리 원칙

1. 퇴사자 계정은 hard delete 대신 `inactive` 또는 `deactivated`로 처리한다.
2. 진행 중 영업이 남아 있으면 먼저 이관 또는 해제가 필요하다.
3. 과거 메모와 소유 이력은 유지한다.

### 5.2 비활성화 순서

1. 진행 중 영업 존재 여부 확인
2. 이관 또는 해제 처리
3. membership 상태 변경
4. 필요 시 account 상태 변경
5. 감사로그 기록

## 6. 영업 claim 운영 정책

### 6.1 기본 원칙

1. 영업 owner 변경은 `release`보다 `transfer`를 기본으로 본다.
2. 영업 이력은 보존한다.
3. 메모는 일반 사용자 삭제 불가를 기본으로 한다.
4. 프로젝트 owner 변경은 release보다 transfer를 먼저 고려한다.

### 6.2 수정/해제/이관

일반 사용자:

1. 본인 claim 건 메모 추가 가능
2. 본인 claim 해제 가능
3. 메모 삭제 불가
4. 정정은 새 메모 추가 방식

관리자:

1. 강제 해제 가능
2. 강제 이관 가능
3. 필요 시 메모 강제 삭제 가능

### 6.2.1 메모 삭제 정책

1. 일반 사용자: 삭제 없음
2. 일반 사용자: 정정은 새 메모 추가로 처리
3. 관리자: 필요 시 강제 삭제 가능

### 6.3 이관 정책

1. 단순 담당 변경은 `transfer`로 처리한다.
2. 기존 메모는 유지한다.
3. 새 담당자는 기존 히스토리를 이어받아 계속 기록한다.
4. 이관 이벤트는 시스템 메모 또는 감사 로그에 남긴다.

### 6.4 종료 상태

- `영업 진행 중`
- `계약 완료`
- `영업 종료`

정책:

1. `해제`는 결과 상태가 아니라 담당 잠금 해제다.
2. `계약 완료`는 수주 성공이다.
3. `영업 종료`는 실패/중단/유실이다.

### 6.5 계약 완료 규칙

1. 계약 완료 시 계약금액 입력이 필수다.
2. 누락 시 저장되지 않아야 한다.
3. 계약금액은 종료/완료 정리 화면에서 확인 가능해야 한다.

### 6.6 사용자 모드 노출 정책

1. `내가 진행 중인 영업`에서는 본인 담당 건만 수정 가능하다.
2. `회사 전체 진행 중인 영업`은 전원 read-only다.
3. `전체 영업 대상 프로젝트`에서는 아직 미배정 신규 대상만 보여준다.
4. 진행 중/계약 완료/영업 종료 프로젝트는 전체 영업 대상 프로젝트에서 숨긴다.

추가 규칙:

1. `회사 전체 진행 중인 영업`은 수정 불가 read-only 패널이다.
2. `내가 진행 중인 영업`에서 수정한 영업현황은 회사 전체 패널에도 동일하게 반영된다.
3. `전체 영업 대상 프로젝트`에서는 영업 시작만 가능하고, 영업현황 편집은 허용하지 않는다.

### 6.7 종료/완료 정리 정책

1. `종료/완료 정리`는 운영 결과 보관용이며 신규 영업 대상 목록과 분리한다.
2. 연도별, 월별로 묶어서 확인한다.
3. 아직 오지 않은 미래 연도는 노출하지 않는다.
4. 계약 완료 건은 계약금액을 함께 보여준다.
5. 영업 종료 건은 추정금액 기준으로 남기고 계약금액은 요구하지 않는다.

## 7. 회원정보 정책

본인 수정 가능:

- `display_name`
- `mobile_phone`
- `office_phone`
- 비밀번호

관리자 수정 가능:

- 역할
- `membership_status`
- `team_name`
- `job_title`

읽기 전용:

- `email`
- `organization_name`

보안 규칙:

- 회원정보 수정 시 현재 비밀번호 확인을 요구한다.

### 7.1 관리자 사용자 관리 정책

1. 관리자만 초대와 사용자 목록 관리에 접근한다.
2. 일반 사용자는 본인 회원정보만 수정한다.
3. 관리자도 bootstrap/platform_admin 계정의 핵심 권한을 임의로 바꾸지 않는다.

### 7.2 회원정보 수정 정책

1. 표시 이름, 휴대폰, 회사 전화 수정에는 현재 비밀번호 확인을 요구한다.
2. 공유된 PC에서 열린 세션을 통한 무단 수정 위험을 줄이는 것이 목적이다.
3. 비밀번호를 모르면 프로필 변경도 완료되지 않아야 한다.

### 7.3 관리자 수정 예외

1. bootstrap/platform_admin 계정의 핵심 전역 권한은 일반 관리자 화면에서 바꾸지 않는다.
2. 조직 관리자는 자기 조직 membership 범위 안에서만 다른 사용자 정보를 수정한다.
3. 본인 membership role을 임의로 낮추거나 올리는 self-edit는 허용하지 않는다.

## 8. 메일 발송 정책

현재 정책:

1. 현재는 `Gmail SMTP`를 임시 운영 채널로 사용한다.
2. 이 방식은 개발/초기 운영용이다.
3. 장기 운영은 `Resend + 회사 도메인 기반 no-reply`로 전환한다.

상세는 [reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](../reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md)를 따른다.

추가 원칙:

1. 기본 Supabase 내장 메일러는 실운영 기본 채널로 보지 않는다.
2. 메일 수신자가 보는 발신 주소는 장기적으로 회사 도메인 발신자여야 한다.
3. 현재는 개발 속도를 위해 임시 SMTP를 허용하되, 정식 운영 전환 계획을 문서에 남긴다.

### 8.1 세션 유지 정책

1. 영업사원 계정은 사용 편의를 위해 장기 로그인 유지를 우선한다.
2. 현재 목표는 PC/모바일에서 최대 30일 수준의 로그인 유지다.
3. 관리자는 필요 시 더 엄격한 세션 정책을 적용할 수 있도록 확장 여지를 남긴다.

### 8.2 메일 공급자 전환 정책

1. 초기 운영은 `Gmail SMTP`를 사용할 수 있다.
2. 장기 운영 목표는 `Resend + 회사 도메인 기반 no-reply 발신 주소`다.
3. 공급자 전환은 문서/템플릿/redirect 정책과 분리하여 SMTP 설정 계층에서 바꿀 수 있어야 한다.
4. 메일 발송 공급자가 바뀌어도 초대 lifecycle과 가입 정책은 바뀌지 않아야 한다.

## 9. 감사로그 정책

최소 이벤트:

- `invite_created`
- `invite_revoked`
- `invite_accepted`
- `membership_role_changed`
- `membership_deactivated`
- `project_transferred`

권장 추가 이벤트:

- `invite_mail_sent`
- `profile_updated`
- `sales_claim_closed_won`
- `sales_claim_closed_lost`
- `sales_claim_released`

### 9.1 감사로그 보존 원칙

1. 감사로그는 운영 판단과 사후 추적을 위한 보존 기록이다.
2. UI에서 보이지 않아도 로그는 내부적으로 남길 수 있다.
3. hard delete보다 비활성화/철회/상태 변경을 선호하는 이유도 감사 추적성 때문이다.

### 9.2 화면 노출과 로그 보존 관계

1. 운영 화면에서 숨긴 항목이 곧 삭제를 의미하지는 않는다.
2. 철회 초대, 강제 삭제 메모, 종료된 영업은 UI에서 축약되거나 숨길 수 있어도 감사로그에는 남긴다.
3. 사용자 UI는 단순화하고, 추적성은 로그와 관리자 화면에서 유지한다.

### 9.3 감사로그 최소 필드 정책

1. 감사로그는 최소 `organization_id`, `actor_user_id`, `event_type`, `target_type`, `target_id`, `created_at`를 가져야 한다.
2. 가능한 경우 `actor_membership_id`를 함께 기록한다.
3. 정책적으로 중요한 변경은 `payload_json`에 before/after 또는 핵심 근거값을 남긴다.
4. 사용자 화면에서는 일부 로그를 숨길 수 있어도, 관리자/감사 기준 기록은 보존한다.

## 10. 부속 reference 문서

- [reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md](../reference/operations/PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md)
- [reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](../reference/operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md)
- [reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](../reference/operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md)

## 11. 다음 통합 대상

향후 아래를 더 흡수한다.

1. 초대/사용자 관리 UI 운영 규칙
2. 관리자/사용자 모드 노출 정책
3. 영업 집계/종료/완료 보존 규칙
4. 메일 템플릿 운영 기준
5. 상태별 사용자 커뮤니케이션 문구 기준

