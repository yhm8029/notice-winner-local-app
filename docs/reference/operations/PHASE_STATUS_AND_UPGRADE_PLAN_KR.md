# Phase 상태 및 판단 기준

## 문서 목적
- 이 문서는 Phase 1과 Phase 2의 경계를 다시 고정한다.
- 현재 구현 상태를 "GUI parity 기준"으로 판단할지, "운영 편의 기능"으로 판단할지 구분한다.

## 핵심 정의
- Phase 1: 현재 GUI와 기능이 동일해야 한다.
- Phase 2: Phase 1에서 맞춘 기능을 여러 사용자가 함께 쓰는 구조를 추가한다.

## 결론
1. Phase 1 완료 판단은 GUI parity 기준으로만 한다.
2. 사용자/관리자 모드, dashboard, parity UI, presets 같은 항목은 운영/사용자 편의 기능으로 분리한다.
3. 운영 편의 기능이 좋아졌더라도 GUI parity가 덜 맞으면 Phase 1 완료가 아니다.

## Phase 1

### 목표
1. 웹 저장소만으로 GUI와 같은 기능을 수행한다.
2. `collect -> filter -> rescan -> export -> tracker_export` 결과가 GUI와 동등해야 한다.
3. `winner_csv`와 `tracking_excel`을 GUI와 같은 수준으로 생성해야 한다.
4. 트래커 핵심 필드가 GUI와 같은 수준으로 채워져야 한다.

### 완료 판단 기준
1. 같은 입력에서 GUI와 같은 기능 흐름이 동작한다.
2. GUI와 같은 수준의 산출물이 나온다.
3. GUI와 같은 수준의 tracker 결과가 나온다.
4. GUI가 사용하는 핵심 fallback, rescue, 후처리 규칙이 동등하게 반영된다.

### 완료 근거 문서
1. [SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md](./SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md)
2. [TECHNICAL_SPEC_GUI_PARITY_KR.md](./TECHNICAL_SPEC_GUI_PARITY_KR.md)
3. [PHASE1_EQUIVALENCE_TEST_CASES_KR.md](./PHASE1_EQUIVALENCE_TEST_CASES_KR.md)

### Phase 1에서 다루지만 아직 항상 증빙해야 하는 항목
1. GUI full parser와 같은 fallback/rescue 동작
2. `LOFIN`, `EAIS`, `HUB`, 교육청 웹 순서의 동등성
3. tracker 기본값 병합과 후처리의 동등성
4. 핵심 tracker 필드의 실데이터 충실도

## 운영/사용자 편의 기능
아래는 Phase 1 완료 조건이 아니라 별도 운영/사용자 편의 문서에서 다룬다.
1. 사용자/관리자 모드
2. dashboard
3. parity report UI
4. recent runs / projects / presets
5. panel modularization
6. 부모 성공 후 child 자동 생성 같은 콘솔 편의 트리거

참고:
- [OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](./OPERATIONS_USER_CONVENIENCE_SPEC_KR.md)

## Phase 2

### 목표
1. Phase 1에서 맞춘 기능을 여러 사용자가 함께 쓸 수 있게 만든다.
2. 인증, 권한, 조직/프로젝트 범위, 충돌 제어를 추가한다.

### 대표 항목
1. 로그인/세션
2. 권한 분리
3. 조직/프로젝트 접근 제어
4. 다중 사용자 충돌 제어
5. 감사/운영 정책 강화

### Phase 2 운영 모델
1. 고객은 `organization` 단위로 관리한다.
2. 사용자는 개인별 `1인 1계정`을 기본 원칙으로 한다.
3. 가입은 자유가입이 아니라 `초대 기반`을 기본값으로 한다.
4. 회사별 사용자 한도는 `active_user_limit`, `pending_invite_limit`으로 관리한다.
5. 권한 계층은 `platform_admin > org_admin > org_member`를 권장한다.
6. 현재 세션 구현은 signed cookie + refresh 기반이며, `단일 활성 세션`은 후속 hardening으로 미룬다.
7. 대형 고객사 확장 경로로 `회사 SSO`를 둔다.

### 세부 명세
- [PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md](./PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md)
- [PHASE2_PLATFORM_LAYER_ARCHITECTURE_KR.md](./PHASE2_PLATFORM_LAYER_ARCHITECTURE_KR.md)
- [PHASE2_DISCUSSION_AND_CURRENT_DESIGN_HANDOFF_KR.md](./PHASE2_DISCUSSION_AND_CURRENT_DESIGN_HANDOFF_KR.md)
- [PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md](./PHASE2_SALES_CLAIM_AND_PIPELINE_SPEC_KR.md)

## Phase 3

### 목표
1. Phase 2에서 만든 조직/권한/seat 모델을 실제 유료 플랜 판매와 연결한다.
2. 결제 승인, 실패, 만료, 연장, 환불 같은 청구 운영 상태를 추가한다.
3. 결제 상태와 서비스 상태를 분리해 운영 가능한 SaaS 과금 구조를 만든다.

### 대표 항목
1. organization 단위 플랜 결제
2. 카드결제 기반 checkout
3. webhook 기반 결제 확정
4. grace period / past_due 운영
5. 결제 이력 / 운영자 override / 환불 메모

### 세부 명세
- [PHASE3_BILLING_AND_PAYMENT_SPEC_KR.md](./PHASE3_BILLING_AND_PAYMENT_SPEC_KR.md)

## 현재 우선순위 해석
1. GUI parity에 직접 영향을 주는 작업은 계속 Phase 1 항목이다.
2. 운영 편의 기능은 GUI parity를 깨지 않는 선에서만 추가한다.
3. 여러 사용자가 함께 쓰는 구조는 Phase 2로 다룬다.
4. 유료 플랜 판매와 청구 운영은 Phase 3로 분리한다.
