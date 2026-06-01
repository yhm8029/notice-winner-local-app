# 화면-API-DB 필드 매핑

- 문서 역할: 화면-API-DB 필드 매핑 참고서
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 각 화면에 보이는 값이 어느 API와 어느 DB/도메인 필드에서 오는가
- 이 문서가 답하지 않는 질문: 최종 계약 우선순위, 전체 알고리즘 설명
- 상위 기준 문서: [../.../../spec/UI_SCREEN_SPEC_KR.md](../.../../spec/UI_SCREEN_SPEC_KR.md), [../.../../spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md](../.../../spec/REBUILD_IMPLEMENTATION_PLAYBOOK_KR.md)
- 충돌 시 우선 문서: [../.../../spec/TECHNICAL_SPEC_KR.md](../.../../spec/TECHNICAL_SPEC_KR.md), [../.../../spec/OPERATIONS_POLICY_KR.md](../.../../spec/OPERATIONS_POLICY_KR.md)

작성일: 2026-03-22  
목적: 화면 재구축 시 필드 출처를 빠르게 찾게 한다.

## 1. 사용 원칙

1. 화면 라벨은 한국어 기준으로 적고, 괄호 안에 핵심 내부 필드를 적는다.
2. API는 현재 구현 이름을 기준으로 적는다.
3. DB는 물리 테이블 또는 read model 기준으로 적는다.

## 2. 로그인/회원정보

| 화면 라벨 | API | 응답/요청 필드 | DB/외부 출처 | 비고 |
| --- | --- | --- | --- | --- |
| 로그인 이메일 | `POST /api/auth/login` | `email` | Supabase Auth | bootstrap 여부는 runtime에서 해석 |
| 현재 사용자 이메일 | `GET /api/auth/session` | `email` | Supabase Auth | 읽기 전용 |
| 표시 이름 | `GET/PATCH /api/auth/profile` | `display_name` | `user_profiles.display_name` | 본인 수정 가능 |
| 휴대폰 | `GET/PATCH /api/auth/profile` | `mobile_phone` | `user_profiles.mobile_phone` | 본인 수정 가능 |
| 회사 전화 | `GET/PATCH /api/auth/profile` | `office_phone` | `user_profiles.office_phone` | 본인 수정 가능 |
| 역할 | `GET /api/auth/session` | `global_role`, `membership_role` | membership 해석 | 사용자 화면에선 한글 라벨화 |
| 회사명 | `GET /api/auth/session` | `organization_name` | `organizations.name` | 읽기 전용 |

## 3. 사용자 초대 및 관리

| 화면 라벨 | API | 응답/요청 필드 | DB 출처 | 비고 |
| --- | --- | --- | --- | --- |
| 이메일 | `POST /api/auth/invitations` | `email` | `invitations.email` | 로그인 이메일과 동일한지 검증 |
| 표시 이름 | `POST /api/auth/invitations` | `display_name` | `invitations.display_name` | 초대 수락 후 profile seed |
| 역할 | `POST /api/auth/invitations` | `role` | `invitations.role` | `org_admin/org_member` |
| 팀명 | `POST /api/auth/invitations` | `team_name` | `invitations.team_name` | 선택 입력 |
| 직책 | `POST /api/auth/invitations` | `job_title` | `invitations.job_title` | 선택 입력 |
| 만료일(일) | `POST /api/auth/invitations` | `expires_in_days` | `invitations.expires_at` | UI는 일수, DB는 시각 |
| 초대 상태 | `GET /api/auth/invitations` | `status` | `invitations.status` | 목록은 주로 pending 기준 |
| 사용자 목록 표시 이름 | `GET /api/auth/users` | `display_name` | `user_profiles.display_name` | |
| 사용자 목록 이메일 | `GET /api/auth/users` | `email` | Supabase/Auth profile 연결 | |
| 사용자 목록 역할 | `GET /api/auth/users` | `membership_role` | `organization_memberships.role` | 한글 라벨 변환 |
| 소속 상태 | `GET/PATCH /api/auth/users` | `membership_status` | `organization_memberships.membership_status` | |
| 팀명/직책 수정 | `PATCH /api/auth/users` | `team_name`, `job_title` | `organization_memberships.team_name`, `job_title` | 관리자만 |

## 4. 실행/로그/산출물

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 실행 ID | `GET /api/runs/{id}` | `id` | `pipeline_runs.id` | |
| 상태 | `GET /api/runs/{id}` | `status` | `pipeline_runs.status` | |
| 진행률 | `GET /api/runs/{id}` | `progress_current`, `progress_total` | `pipeline_runs` | |
| 현재 단계 | `GET /api/runs/{id}` | `progress_stage` | `pipeline_runs` | |
| run type | `GET /api/runs/{id}` | `run_type` | `pipeline_runs.run_type` | `project_tracker`, `tracker_export` |
| 로그 항목 | `GET /api/runs/{id}/logs` | `message`, `stage`, `created_at` | `pipeline_logs` | |
| 아티팩트 다운로드 | `GET /api/runs/{id}/artifacts` | `artifact_id`, `download_url`, `type` | `run_artifacts`, storage | |

## 5. tracker 보드

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 프로젝트명 | `GET /api/tracker-entries` | `project_name` | tracker effective view | |
| 연면적/규모 | `GET /api/tracker-entries` | `gross_area_scale` | tracker effective view | |
| 공사비 | `GET /api/tracker-entries` | `construction_cost` | tracker effective view | |
| 빌딩자동제어 추정금액 | `GET /api/tracker-entry-summaries` 또는 entries | `building_automation_estimated_amount` | tracker effective view | |
| 설계사무소 | `GET /api/tracker-entries` | `architect_office` | tracker effective view | |
| 개찰예정일/착공일 | `GET /api/tracker-entries` | `construction_start_date` 등 | tracker effective view | |
| 담당 | `GET /api/tracker-entries` | `demand_contact` | tracker effective view | |
| 현장 | `GET /api/tracker-entries` | `site_location_1/2` 조합 | tracker effective view | |
| 수정 저장 | `PATCH /api/tracker-entries/{id}` | override payload | override store + audit | 관리자만 |

## 6. 내가 진행 중인 영업

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 카드 프로젝트명 | `GET /api/sales-claims` | `project_name` | sales claim read model + tracker source | |
| 공사비/연면적/추정금액 | `GET /api/sales-claims` | summary fields | tracker source snapshot | |
| 영업 시작 | `GET /api/sales-claims` | `claimed_at` | `project_sales_claims.claimed_at` | UI는 KST 날짜 변환 |
| 현재 담당 시작 | `GET /api/sales-claims` | `current_owner_assigned_at` | `project_sales_claims.current_owner_assigned_at` | |
| 최근 메모 목록 | `GET /api/sales-claims` | `notes` | `project_sales_claim_events` | append-only |
| 메모 입력 | `PATCH /api/sales-claims/{project_id}` | `note` | events append | owner만 가능 |
| 담당 이관 | `POST /api/sales-claims/{project_id}/transfer` | `to_user_id` | claims + events | |
| 계약 완료 | `POST /api/sales-claims/{project_id}/close` | `status=won`, `contract_amount_text` | claims + events | 금액 필수 |
| 영업 종료 | `POST /api/sales-claims/{project_id}/close` | `status=lost` | claims + events | |
| 해제 | `POST /api/sales-claims/{project_id}/release` | n/a | claims + events | |

## 7. 회사 전체 진행 중인 영업

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 운영자 | `GET /api/sales-claims` | `owner_display_name`, `owner_email` | membership/profile join | 읽기 전용 |
| 최근 영업현황 | `GET /api/sales-claims` | latest note summary | events | 읽기 전용 |
| 상태 배지 | `GET /api/sales-claims` | `claim_status` | `project_sales_claims.claim_status` | |

## 8. 전체 영업 대상 프로젝트

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 카드 목록 | `GET /api/tracker-entry-summaries` | summary fields | tracker read model | 진행 중/종료/완료 제외 |
| 영업 버튼 | `POST /api/sales-claims/{project_id}/claim` | n/a | claims/events | 미배정 대상만 노출 |

## 9. 영업사원별 진행 현황

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 영업사원 이름 | `GET /api/sales-claims/summary-by-user` | `owner_display_name` | membership/profile join | 관리자 모드 |
| 진행 건수 | same | `active_count` | claims aggregate | |
| 총 추정금액 | same | `estimated_amount_total_text` | tracker summary aggregate | |
| 프로젝트별 항목 | same | list items | claims + tracker summary | |
| 강제 해제 | `POST /api/sales-claims/{project_id}/release` | admin override | claims/events | 관리자만 |

## 10. 종료/완료 정리

| 화면 라벨 | API | 응답 필드 | DB/출처 | 비고 |
| --- | --- | --- | --- | --- |
| 연도/월 그룹 | `GET /api/sales-claims/summary-by-user` 또는 closed summary | `closed_at` | claims/events | 미래 연도 비노출 |
| 계약 완료 항목 | same | `status=won` | claims/events | 계약금액 표시 |
| 영업 종료 항목 | same | `status=lost` | claims/events | |
| 계약금액 | same | `contract_amount_text` | close event payload | 콤마 포맷 표시 |

## 11. 다운로드

| 화면 라벨 | API | 응답 필드 | 출처 | 비고 |
| --- | --- | --- | --- | --- |
| 내가 진행 중인 영업 엑셀 다운로드 | `GET /api/sales-claims/export?scope=my` | binary workbook | local tracker template + current claim rows | |
| 회사 전체 진행 중인 영업 엑셀 다운로드 | `GET /api/sales-claims/export?scope=company` | binary workbook | same | |
| tracker 엑셀 다운로드 | artifact download | binary workbook | tracker export child run artifact | |


