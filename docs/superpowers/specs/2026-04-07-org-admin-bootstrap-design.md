# Org Admin Bootstrap Design

## Goal

운영자 패널 초기 진입 시 `members`, `invitations`, `auth audit logs`, `download audit logs`, `login audit logs`를 각각 따로 불러오지 않고, 한 번의 bootstrap 응답과 캐시 우선 렌더로 체감 지연과 프런트 timeout 가능성을 줄인다.

## Current Problem

- 운영자 패널은 현재 개별 API 다섯 개를 순차 호출한다.
- timeout burst는 줄었지만, 화면은 카드별로 천천히 채워져 보인다.
- 프로덕션 auth/session 경로가 느릴 때 초기 패널 체감도 같이 나빠진다.

## Recommended Approach

### Backend

- `GET /api/admin/organization-panel-bootstrap` 추가
- 관리자만 접근 가능
- 아래 데이터를 한 응답으로 반환
  - `members`
  - `plan_summary`
  - `invitations`
  - `auth_audit_logs`
  - `download_audit_logs`
  - `login_audit_logs`
- 각 리스트는 현재 UI가 보이는 기본 개수 기준으로 잘라서 반환하되, `has_more` 플래그를 같이 포함한다.
- 기존 개별 API는 유지한다. 더보기/개별 새로고침은 기존 경로를 계속 쓴다.

### Frontend

- 운영자 패널 초기 진입 시 bootstrap API만 호출한다.
- localStorage에 bootstrap payload를 저장한다.
- 패널 렌더 시
  - 캐시가 있으면 즉시 적용
  - 이후 네트워크 bootstrap으로 최신화
- 개별 로더는 유지하되, 초기 진입 시에는 bootstrap 경로가 우선이다.
- 캐시 데이터는 stale 허용으로 읽고, auth/admin 문맥이 아니면 즉시 폐기한다.

## Data Shape

- `members: AuthOrganizationUserItem[]`
- `plan_summary: AuthOrganizationPlanSummary | null`
- `invitations: AuthInvitationItem[]`
- `auth_audit_logs: { items: AuthAuditLogItem[], has_more: bool }`
- `download_audit_logs: { items: DownloadAuditLogItem[], has_more: bool }`
- `login_audit_logs: { items: LoginAuditLogItem[], has_more: bool }`
- `generated_at: string`

## Error Handling

- bootstrap endpoint 실패 시 기존 개별 로더 fallback을 허용한다.
- 캐시가 있으면 에러여도 cached 상태를 유지하고 flash만 띄운다.
- 캐시가 없으면 기존 로딩/에러 렌더를 그대로 사용한다.

## Verification

- backend endpoint 응답 shape/권한 테스트
- frontend bootstrap loader가 캐시를 즉시 적용하는지 테스트
- frontend bootstrap loader가 네트워크 성공 후 상태와 캐시를 갱신하는지 테스트
- 기존 개별 로더 회귀 없음 확인
