# Phase 3 결제 및 청구 운영 명세

## 연관 문서
- [PHASE_STATUS_AND_UPGRADE_PLAN_KR.md](./PHASE_STATUS_AND_UPGRADE_PLAN_KR.md)
- [PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md](./PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md)
- [api-spec.md](./api-spec.md)
- [db-schema.md](./db-schema.md)

이 문서는 Phase 2에서 만든 `organization`, `plan_code`, `active_user_limit`, `pending_invite_limit` 운영 모델 위에, 실제 유료 플랜 판매와 결제 반영 정책을 덧붙여 고정한다.

## 1. 목표

Phase 3의 목표는 "결제 버튼 추가"가 아니다.

1. 회사(`organization`) 단위 플랜을 실제 유료 상태와 연결한다.
2. 결제 성공/실패/취소/환불과 서비스 상태를 분리해서 관리한다.
3. 결제 완료 여부는 프론트 콜백이 아니라 서버 검증과 webhook 기준으로 확정한다.
4. 결제 이력, 플랜 변경, 운영자 override를 감사 가능하게 남긴다.
5. 초기 출시 범위를 작게 잡아 구현/운영 복잡도를 통제한다.

## 2. 범위

Phase 3 MVP에 포함:

1. `organization` 단위 유료 플랜 구매
2. `org_admin` 기준 결제 진입
3. 카드 결제 기반 유료 플랜 전환
4. 결제 결과에 따른 `plan_code` / limit 반영
5. 결제 이력 조회
6. webhook 기반 결제 상태 확정
7. 운영자(`platform_admin`)의 수동 override / 수동 연장 / 환불 메모 기록
8. 만료 예정 / 결제 실패 / 연장 필요 배너와 관리자 화면 요약

Phase 3 MVP에서 제외:

1. 자동 세금계산서 발행
2. 계좌이체 / 가상계좌 / 후불 청구
3. 다중 통화 / 해외 결제
4. 조직별 커스텀 단가 협상 UI
5. 인앱 자동 proration 계산
6. 카드 자동 정기결제(billing key) 의무화
7. 회계 ERP 직접 연동

핵심 원칙:

- 초기는 `카드결제 only`로 간다.
- 결제 증빙 기본값은 카드 매출전표/영수증이다.
- 세금계산서 자동화는 Phase 3 MVP 범위에 넣지 않는다.
- 복잡한 구독 과금보다 `결제 상태와 서비스 상태의 정합성`을 먼저 고정한다.

### 2.1 PG / 결제사 선택 원칙

Phase 3A 기본 선택:

1. `PortOne` 같은 결제 추상화 레이어를 우선 검토한다.
2. 이유는 문서 구조가 이미 `provider` 필드, provider별 webhook, provider-aware 거래 이력을 전제로 하기 때문이다.
3. 속도가 최우선이고 장기간 단일 PG만 쓸 확신이 있으면 특정 PG direct 연동도 가능하다.

정리:

- Phase 3A 기본 방향은 `단일 PG 고정`보다 `provider-aware 구조`다.
- 따라서 API와 DB는 특정 PG 고유 용어보다 provider 중립 구조를 우선한다.

## 3. 단계 해석

Phase 2가 "여러 사용자가 함께 쓰는 SaaS 운영 구조"를 만드는 단계였다면, Phase 3는 그 구조를 실제 매출과 연결하는 단계다.

정리:

1. Phase 2: 로그인, 초대, 좌석 한도, 권한, 감사 로그
2. Phase 3: 유료 플랜, 결제 승인, 결제 실패, 만료, 연장, 환불, 결제 운영

## 4. 상품 모델

초기 상품 모델:

1. 과금 주체는 `organization`
2. 결제 권한 기본값은 `org_admin`
3. 현재 `plan_code` 체계(`A`, `B`, `C`)를 유지한다
4. 각 플랜은 `active_user_limit`, `pending_invite_limit`를 가진다
5. 표시용 상품명은 별도 필드(`plan_display_name`)로 분리할 수 있다

권장 예:

1. `A`
   - 소규모 팀
   - 활성 사용자 5
   - pending 초대 5
2. `B`
   - 일반 팀
   - 활성 사용자 10
   - pending 초대 10
3. `C`
   - 확장 조직
   - 활성 사용자 100
   - pending 초대 100

중요:

- 서비스 로직은 계속 `plan_code`와 limit 값을 읽는다.
- 결제 시스템은 "어떤 상품을 샀는지"와 "언제까지 유효한지"를 관리한다.
- 실제 제한 enforcement의 single source of truth는 계속 서버 쪽 limit 필드다.
- `상품 카탈로그의 기준값`과 `organization에 실제 적용된 현재값`은 구분한다.
- 할인, 예외 계약, 수동 override가 있어도 `organizations.plan_code/limit`에는 현재 적용 결과값만 남긴다.

## 5. 과금 정책

Phase 3 MVP 권장 정책:

1. 결제 수단은 카드만 허용한다.
2. 초기에는 `수동 연장형 월간 결제`를 기본값으로 둔다.
3. 자동 정기결제는 후속 단계(`Phase 3B`)로 미룬다.
4. 업그레이드는 결제 성공 직후 즉시 반영한다.
5. 다운그레이드는 다음 결제 주기부터 반영한다.
6. 환불과 강제 취소는 `platform_admin` 운영 기능으로 시작한다.

왜 수동 연장형으로 시작하나:

1. billing key, 자동 재시도, 카드 갱신 실패 처리 복잡도를 늦출 수 있다.
2. 고객이 실제로 유료 전환하는지 먼저 확인할 수 있다.
3. seat / invite / 플랜 상태와 결제 이벤트의 연결을 먼저 안정화할 수 있다.

명시:

- Phase 3A는 `구독형 자동청구`가 아니다.
- Phase 3A는 `월 단위 유효기간을 가진 수동 연장형 과금`이다.
- 따라서 만료 전 갱신은 자동 청구가 아니라 사용자 또는 운영자 액션으로 시작한다.
- Phase 3A self-serve 상품은 `월간만` 연다.
- 연간 플랜이 필요하면 우선 `platform_admin` 수동 조정 또는 별도 영업 예외로 처리한다.

## 6. 결제 상태와 서비스 상태

Phase 3에서는 결제 상태와 서비스 상태를 분리한다.

### 6.1 결제 거래 상태(`payment_transaction_status`)

1. `checkout_requested`
2. `checkout_pending`
3. `authorized`
4. `paid`
5. `failed`
6. `cancelled`
7. `refunded`
8. `partially_refunded`

### 6.2 조직 청구 상태(`billing_status`)

1. `trial`
2. `active`
3. `grace_period`
4. `past_due`
5. `cancelled`

원칙:

1. 프론트의 결제 성공 화면만으로 `billing_status=active`로 바꾸지 않는다.
2. 서버 검증 또는 webhook에서 `paid`가 확정된 뒤에만 플랜을 반영한다.
3. `payment_transaction_status`는 거래 단위 이력이다.
4. `billing_status`는 조직의 현재 서비스 상태다.

## 7. 만료와 연체 정책

권장 초기 정책:

1. 유료 기간 종료 전 `D-7`, `D-3`, `D-1` 배너/이메일 안내
2. 종료 후 `grace_period` 7일
3. `grace_period` 중에는 기존 사용자 읽기/기존 핵심 기능은 유지
4. `grace_period` 중에는 신규 seat 증가, 신규 초대, 플랜 업그레이드 없는 추가 사용 확대를 막는다
5. `past_due` 진입 후에는 read-only 중심 모드로 내린다

초기 간단 정책으로 더 줄이고 싶다면:

- `active -> grace_period -> past_due(read-only)` 3단계만 먼저 구현한다.

### 7.1 `grace_period`

허용:

1. 기존 사용자 로그인
2. 기존 데이터 조회
3. 핵심 읽기 기능 사용
4. Billing 화면 진입
5. 재결제 / 연장 / 업그레이드 결제

차단:

1. 신규 초대
2. 신규 seat 증가를 유발하는 활성화
3. 플랜 한도 밖의 추가 사용 확대

### 7.2 `past_due`

기본 원칙:

- `past_due`는 read-only 상태다.
- 단, Billing 복구를 위한 화면 진입과 결제 액션은 예외적으로 허용한다.

허용:

1. 로그인
2. 읽기 전용 조회
3. Billing 화면 진입
4. 결제 이력 조회
5. 실패 사유 확인
6. 영수증 / 결제 결과 링크 이동
7. 결제 복구 액션
8. 운영자 복구 조치

차단:

1. 신규 실행 생성
2. tracker 수정
3. 초대 생성 / 철회 / 활성화
4. 업로드 / 변경 / 백그라운드 작업 생성
5. 일반 운영 데이터 변경

주의:

- `past_due`의 read-only 예외는 결제 복구와 상태 확인에 필요한 Billing 동작으로 한정한다.
- 일반 비즈니스 데이터 수정 권한이 복구 예외로 넓어지면 안 된다.

## 8. 역할 정책

### 8.1 `org_admin`

가능:

1. 자기 조직 결제 화면 접근
2. 플랜 선택
3. 결제 시작
4. 결제 이력 조회
5. 연장/재결제 실행

불가:

1. 환불 강제 승인
2. 다른 조직 결제 조회
3. limit override

### 8.2 `platform_admin`

가능:

1. 전체 조직 결제 상태 조회
2. 수동 플랜 조정
3. 결제 실패 복구 메모
4. 환불/취소 기록
5. grace / past_due 운영 전환
6. 예약 다운그레이드 해제 / 변경

### 8.3 `org_member`

가능:

1. 현재 플랜/제한 요약 읽기

불가:

1. 결제 시작
2. 플랜 변경
3. 결제수단 변경

## 9. 주요 사용자 흐름

### 9.1 신규 유료 전환

1. `org_admin`이 Billing 화면 진입
2. 현재 플랜, 현재 활성 사용자 수, 한도, 다음 결제 예정일 확인
3. 업그레이드할 플랜 선택
4. 서버가 checkout session / payment intent를 생성
5. 사용자가 PG 결제 화면으로 이동
6. PG 완료 후 프론트는 결과 페이지로 복귀
7. 서버는 webhook 또는 서버 검증으로 결제 확정 여부를 확인
8. 확정 후 `organization`의 `plan_code`, `active_user_limit`, `pending_invite_limit`, `billing_period_end`, `billing_status`를 갱신
9. 감사 로그와 결제 거래 이력을 남긴다

### 9.2 연장

1. 현재 플랜 유지 상태에서 같은 플랜을 재결제
2. 성공 시 `billing_period_end`를 다음 주기로 연장
3. 연장 전후 상태를 audit log에 남긴다

### 9.3 업그레이드

1. 상위 플랜 선택
2. 결제 성공 즉시 상향 limit 적용
3. 기존 초대/활성 사용자 수가 이미 낮은 제한을 넘어도 문제 없음

### 9.4 다운그레이드 예약

1. 하위 플랜 선택
2. 즉시 적용하지 않고 `next_plan_code`로 예약
3. 다음 갱신 시점에 active seat 수가 하위 한도 이하인지 검증
4. 초과 중이면 다운그레이드를 보류하고 관리자 정리 안내를 띄운다
5. 보류 시 현재 `plan_code`와 현재 `billing_status`는 유지한다
6. 보류 시 `next_plan_code` 예약 상태도 유지한다
7. 조건이 충족되기 전까지 `보류`는 `실패`가 아니라 `대기`로 해석한다

### 9.5 결제 실패

1. 실패 거래는 `payment_transactions`에 남긴다
2. `organization`의 현재 유효 플랜은 즉시 변경하지 않는다
3. 만료 시점이 지나면 `grace_period` 또는 `past_due` 정책으로 이동한다

### 9.6 환불 / 취소

1. MVP에서는 `platform_admin` 수동 운영으로 시작한다
2. 환불이 일어나도 과거 거래 이력은 삭제하지 않는다
3. 서비스 제한 시점은 환불 정책에 따라 운영자가 결정하고 reason을 남긴다

## 10. UI 요구사항

### 10.1 관리자 Billing 화면

필수 카드:

1. 현재 플랜
2. 현재 활성 사용자 수 / 한도
3. 현재 pending 초대 수 / 한도
4. 현재 청구 상태
5. 현재 결제 주기 시작일 / 종료일
6. 다음 적용 예정 플랜(예약 다운그레이드가 있으면)

필수 액션:

1. 플랜 선택
2. 결제 시작
3. 결제 이력 조회
4. 영수증/결제 결과 링크 이동
5. 재결제
6. 운영 문의 진입

필수 메시지:

1. 한도 초과 시 업그레이드 유도 문구
2. 만료 예정 안내
3. 결제 실패 안내
4. grace / past_due 상태 배너

복구 UX 원칙:

1. 1차 복구 경로는 `Billing 화면에서 즉시 재결제`다
2. 반복 실패, 카드 이슈, 환불/취소, 수동 청구 요구는 `운영 문의`로 넘긴다
3. 즉 self-serve를 기본값으로 두되 운영 개입 경로를 보조 경로로 둔다

### 10.2 운영자 Billing 관리 화면

필수 기능:

1. 조직별 결제 상태 검색
2. 최근 실패 거래 조회
3. 수동 플랜 조정
4. 수동 기간 연장
5. 환불/취소 메모 기록
6. 예약 다운그레이드 해제 / 변경

## 11. API 초안

권장 API:

1. `GET /api/billing/summary`
   - 현재 조직 billing 상태, plan, limit, 결제 주기 반환
2. `GET /api/billing/transactions`
   - 현재 조직 결제 이력 반환
3. `POST /api/billing/checkout`
   - 선택한 플랜으로 checkout 생성
4. `POST /api/billing/webhooks/{provider}`
   - PG webhook 수신
5. `POST /api/billing/renew`
   - 현재 플랜 수동 연장 결제 시작
6. `POST /api/billing/change-plan`
   - 업그레이드 즉시 결제 또는 다운그레이드 예약
7. `POST /api/admin/billing/override`
   - `platform_admin` 전용 수동 조정

API 원칙:

1. callback URL hit만으로 상태 확정 금지
2. webhook event는 idempotent 처리
3. 같은 거래 ID에 대한 중복 webhook은 한 번만 반영
4. 권한 검사는 backend 기준으로 강제
5. provider 선택은 서버가 허용 목록 기준으로 검증한다

## 12. DB 모델 초안

기존 유지:

- `organizations.plan_code`
- `organizations.active_user_limit`
- `organizations.pending_invite_limit`

해석 원칙:

1. 상품 카탈로그의 기본 플랜 정의는 별도 기준표 또는 서버 상수로 관리한다.
2. `organizations.plan_code`와 limit 필드는 현재 조직에 실제 적용된 결과값이다.
3. `organization_billing`과 `payment_transactions`는 왜 그 결과값이 되었는지 설명하는 청구 이력이다.
4. 따라서 상품 정의 변경과 조직 적용값 변경은 같은 의미로 취급하지 않는다.
5. 연간/월간 같은 billing cadence는 상품 카탈로그 또는 billing 설정에 두고, `organizations` 제한 필드와 분리한다.

신규 권장 테이블:

### 12.1 `organization_billing`

현재 조직의 billing 스냅샷:

- `organization_id`
- `billing_status`
- `current_plan_code`
- `next_plan_code`
- `billing_period_start`
- `billing_period_end`
- `grace_until`
- `last_paid_at`
- `last_payment_transaction_id`
- `billing_contact_name`
- `billing_contact_email`
- `company_name`
- `business_registration_no` nullable
- `receipt_preference`
- `updated_at`

### 12.2 `payment_transactions`

거래 이력:

- `id`
- `organization_id`
- `provider`
- `provider_transaction_id`
- `provider_checkout_id`
- `requested_plan_code`
- `applied_plan_code`
- `amount`
- `currency`
- `status`
- `requested_by_user_id`
- `paid_at`
- `failed_at`
- `cancelled_at`
- `refunded_at`
- `failure_code`
- `failure_message`
- `raw_response_json`
- `created_at`

### 12.3 `payment_webhook_events`

webhook 수신 이력:

- `id`
- `provider`
- `provider_event_id`
- `event_type`
- `organization_id` nullable
- `transaction_id` nullable
- `payload_json`
- `processed_at`
- `processing_status`
- `error_message`
- `created_at`

### 12.4 `billing_admin_actions`

운영 조치 기록:

- `id`
- `organization_id`
- `actor_user_id`
- `action_type`
- `before_json`
- `after_json`
- `reason`
- `created_at`

## 13. 상태 반영 원칙

결제와 플랜 반영은 아래 순서를 지켜야 한다.

1. checkout 생성
2. 사용자가 PG 결제 진행
3. 서버가 webhook 또는 서버 검증으로 결제 결과 수신
4. 거래 상태 확정
5. 같은 트랜잭션 안에서 `organization_billing`과 `organizations` 반영
6. 감사 로그 기록

중요:

- `organizations`의 plan/limit 필드는 "현재 서비스에 적용된 진실값"이다.
- `payment_transactions`는 이 값이 왜 바뀌었는지 설명하는 원인 기록이다.
- 둘이 어긋나면 서비스 제한이 잘못 걸리므로, 반영 로직은 원자적으로 처리해야 한다.

## 14. 운영 정책

### 14.1 카드결제 only

초기 운영 원칙:

1. 법인카드 / 개인카드 모두 허용
2. 서비스는 카드 영수증/매출전표를 기본 증빙으로 안내
3. 세금계산서 자동 발행은 제공하지 않는다
4. 세금계산서가 필요한 고객은 운영 문의 또는 엔터프라이즈 수동 청구 플로우로 분리한다

### 14.2 사업자 정보 수집

초기 수집 권장:

1. 회사명
2. 결제 담당자명
3. 결제 담당자 이메일
4. 사업자등록번호(nullable)

원칙:

- 사업자 정보는 결제 증빙/운영 문의를 돕는 용도다.
- 사업자등록번호가 없다고 카드결제를 막지는 않는다.
- 필수값은 최소화하고, 자동 세무 처리까지 확장하지 않는다.
- 전화번호, 주소 같은 추가 필드는 MVP 필수값으로 두지 않는다.

### 14.3 영수증/문서

초기 정책:

1. 결제 완료 화면에서 결제 영수증 링크 또는 PG 제공 문서 링크를 노출
2. 조직 관리자 Billing 화면에서 최근 결제 내역과 상태를 다시 볼 수 있어야 한다
3. 별도 세금계산서 PDF 생성은 MVP 범위 밖이다

## 15. 보안 및 무결성 요구사항

1. webhook endpoint는 provider signature 검증이 필요하다
2. 거래 상태 반영은 idempotent 해야 한다
3. 임의 callback 호출만으로 결제 완료 처리되면 안 된다
4. 다른 조직 결제 이력 조회는 backend에서 차단해야 한다
5. 환불 / 취소 / override는 감사 로그와 운영 메모를 남겨야 한다
6. 가격, 플랜 코드, 금액은 서버에서 최종 검증해야 한다
7. 클라이언트가 전달한 금액을 그대로 신뢰하면 안 된다

## 16. 단계별 출시 권장안

### Phase 3A

1. 카드 단건 결제
2. 수동 연장형 월간 플랜
3. webhook 확정
4. 결제 이력
5. 운영자 override
6. Billing self-serve 복구

### Phase 3B

1. 자동 정기결제(billing key)
2. 실패 시 자동 재시도
3. 결제수단 교체
4. 다운그레이드 예약 자동 처리

### Phase 3C

1. 세금계산서/청구 문서 고도화
2. 엔터프라이즈 수동 청구 플로우
3. 회계/ERP 연동

## 17. 리뷰 포인트

이번 문서를 리뷰할 때 먼저 봐야 할 포인트:

1. Phase 3A를 `PortOne 우선 + 카드 단건 결제 + 수동 연장형 월간 과금`으로 고정하는 게 맞는지
2. `active -> grace_period -> past_due(read-only + Billing 복구만 허용)` 정책이 제품 운영에 맞는지
3. `organizations.plan_code/limit`를 계속 서비스 진실값으로 두고 상품 카탈로그와 분리하는 구조가 맞는지
4. `org_admin` self-serve + `platform_admin` override 조합이 운영에 충분한지
5. 세금계산서 자동화를 Phase 3 MVP에서 제외하고 운영 문의 / 수동 청구로 분리하는 것이 맞는지

## 18. 결론

Phase 3 MVP는 복잡한 정기결제 전체를 한 번에 해결하는 단계가 아니다.

우선순위:

1. 유료 플랜 전환
2. 카드결제 확정
3. webhook 기준 상태 반영
4. 조직 limit와 결제 상태 정합성 보장
5. 운영자가 복구 가능한 감사 가능한 구조

그 뒤에 자동 정기결제와 세무 자동화를 올리는 순서가 맞다.
