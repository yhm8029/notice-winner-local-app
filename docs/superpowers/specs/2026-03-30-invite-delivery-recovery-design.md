# Invite Delivery Recovery Design

## Goal

조직 관리자 초대 생성 시 자동 메일 발송을 다시 활성화하고, 발송 실패 시에도 초대 링크와 초기 암호를 관리자 UI에서 즉시 복사할 수 있게 복구한다.

## Scope

- `Gmail SMTP` 기반 자동 초대 메일 발송이 실제로 켜지도록 초대 생성 경로를 점검하고 복구한다.
- 초대 생성 응답에 포함된 `invite_url`, `initial_password`, `delivery_status`, `delivery_message`가 프론트의 사용자 초대 패널에서 항상 보이도록 정리한다.
- 자동 발송 실패 시에도 관리자가 빈 상태를 보지 않고 수동 전달 정보를 즉시 복사할 수 있어야 한다.

## Non-Goals

- 초대 메일 발송 채널을 앱 직접 SMTP로 재설계하지 않는다.
- Supabase Auth 기반 초대 흐름 자체를 다른 공급자로 바꾸지 않는다.
- 초대 승인, 비밀번호 설정, 초대 목록 권한 정책은 이번 범위에서 바꾸지 않는다.

## Current Problems

1. 초대 생성 API가 `send_email = invitation_email_delivery_enabled()` 결과에 따라 `manual` 경로로 떨어질 수 있다.
2. 현재 운영 목표는 `Supabase Auth + Custom SMTP(Gmail)`인데, 실제 실행 경로가 비활성화로 고정되면 자동 발송이 전혀 일어나지 않는다.
3. 프론트 `사용자 초대` 패널은 초대 생성 후 실패/수동 전달 정보를 빈 영역으로 남겨, 관리자가 `invite_url`과 `initial_password`를 복사할 수 없다.

## Design

### Backend

- 초대 생성 엔드포인트의 `send_email` 활성화 판단을 검증하고, 현재 운영 의도에 맞게 자동 발송이 켜지는 조건을 복구한다.
- 초대 생성 서비스는 지금처럼 `invite_url`, `initial_password`, `delivery_status`, `delivery_message`를 항상 채운다.
- 자동 발송 실패 시 `delivery_status = failed`와 사람이 읽을 수 있는 `delivery_message`를 유지한다.
- 자동 발송 비활성 또는 실패 상태에서도 응답 payload는 수동 전달에 필요한 값을 절대 비우지 않는다.

### Frontend

- `사용자 초대` 패널은 초대 생성 직후 응답의 `invite_url`, `initial_password`, `delivery_message`를 시각적으로 노출한다.
- `delivery_status`가 `manual` 또는 `failed`이면 링크 복사와 초기 암호 복사/노출을 강조한다.
- `delivery_status`가 `sent`여도 링크 복사 fallback은 남긴다.
- 스크린샷처럼 빈 카드/빈 박스만 남는 상태는 허용하지 않는다.

## Error Handling

- Gmail SMTP 또는 Supabase Auth 초대 발송에서 예외가 나면 초대 생성 자체는 유지하고 `failed` 상태로 응답한다.
- 프론트는 실패 메시지와 함께 `invite_url`, `initial_password`를 계속 표시한다.
- 복사 실패는 기존 flash/error 처리 패턴을 따른다.

## Testing

- 백엔드
  - 자동 발송 활성/비활성 분기 테스트
  - 발송 실패 시 `failed` + fallback payload 유지 테스트
- 프론트
  - 초대 생성 응답에 `invite_url`/`initial_password`가 있을 때 패널이 값을 렌더하는지 테스트
  - `manual`/`failed` 상태에서 복사 버튼이나 복사 가능한 텍스트가 비지 않는지 테스트

## Success Criteria

- 조직 관리자 초대 생성 후 자동 메일 발송이 켜진 환경에서는 `delivery_status = sent` 또는 실제 발송 시도 결과가 나온다.
- 자동 발송 실패나 비활성 상태에서도 관리자 화면에 초대 링크와 초기 암호가 보여 복사 전달이 가능하다.
- 사용자 입장에서 빈 상태만 보이는 초대 생성 결과는 더 이상 나오지 않는다.
