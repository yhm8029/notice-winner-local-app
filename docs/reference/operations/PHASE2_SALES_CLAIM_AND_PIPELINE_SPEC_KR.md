# Phase 2 영업 점유/영업현황 기술명세서

- 문서 역할: 영업 점유/영업현황 재료 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: Phase 2 영업 점유/영업현황 기능을 어떤 규칙과 구조로 구현할 것인가
- 상위 기준 문서: [02_FUNCTIONAL_SPEC_KR.md](../../spec/FUNCTIONAL_SPEC_KR.md), [05_OPERATION_POLICY_SPEC_KR.md](../../spec/OPERATIONS_POLICY_KR.md)
- 충돌 시 우선 문서: [05_OPERATION_POLICY_SPEC_KR.md](../../spec/OPERATIONS_POLICY_KR.md)

## 1. 문서 목적
- 본 문서는 `Phase 2` 로그인/권한 구조 위에 올라가는 `영업 점유(sales claim)` 기능의 기술 명세를 정의한다.
- 목표는 사용자별로 특정 프로젝트의 영업 담당을 명확히 잠그고, 영업 진행 현황을 공유하며, 관리자 화면에서 영업사원별 진행 건과 추정 금액을 집계할 수 있게 만드는 것이다.
- 1차 구현은 `in-memory` 저장으로 빠르게 동작을 검증한다.
- 단, 나중에 `Supabase/Postgres`로 영속화할 수 있도록 DB 테이블 구조와 API 계약을 지금 문서에 함께 정의한다.

## 2. 기능 목표
1. 사용자 계정 `1`, `2`, `3`처럼 여러 영업 사용자가 각각 로그인할 수 있어야 한다.
2. 어떤 사용자가 특정 프로젝트에 대해 `영업`을 시작하면, 다른 사용자도 그 프로젝트가 이미 누군가의 담당인지 바로 알 수 있어야 한다.
3. 한 프로젝트는 한 시점에 한 명만 영업 담당이 될 수 있어야 한다.
4. 영업 담당자는 해당 프로젝트 카드 안에서 `영업현황`을 직접 입력/저장할 수 있어야 한다.
5. 영업 시작 시점의 `날짜/시간`이 기록되어야 한다.
6. 관리자 모드에서는 영업사원별로 현재 진행 중인 프로젝트 목록, 영업 시작일, 경과일, 추정 금액, 총 추정 금액을 볼 수 있어야 한다.

## 3. 범위

### 3.1 1차 구현 범위
- 로그인된 사용자 기준 영업 점유/해제
- 사용자 모드 `프로젝트 현황` 카드에서 영업 시작
- 영업 담당자만 `영업현황` 수정 가능
- 같은 프로젝트에 대한 중복 영업 시작 차단
- 관리자 모드 집계 패널
- 저장소는 `in-memory`

### 3.2 2차 구현 범위
- Supabase/Postgres 영속 저장
- 감사 로그 영속화
- 조직별 권한 연동
- 회사 관리자/플랫폼 관리자 강제 해제
- 좌석/조직별 영업 집계

## 4. 핵심 결정

### 4.1 잠금 기준은 `entry_id`가 아니라 `project_id`
- 영업 점유의 기준 키는 `project_id`로 한다.
- 이유:
  - 같은 프로젝트가 트래커/프로젝트 카드에 여러 row로 노출될 수 있다.
  - `entry_id` 기준 잠금을 쓰면 같은 프로젝트가 다른 row에서 다시 영업 시작될 수 있다.
  - 영업 현업 관점에서는 “이 row를 누가 맡았나”보다 “이 프로젝트를 누가 맡았나”가 더 중요하다.

### 4.2 대표 row는 별도 보관
- 잠금 기준은 `project_id`지만, 사용자가 어느 카드에서 영업을 시작했는지 추적하기 위해 `source_entry_id`는 함께 저장한다.
- 즉:
  - `claim_key` = `(organization_id, project_id)`
  - `source_entry_id` = 사용자가 실제로 클릭한 대표 row

### 4.3 해제 권한
- `본인`은 자기 영업 건을 해제할 수 있다.
- `관리자`는 다른 사람의 영업 건도 강제 해제할 수 있다.
- 일반 사용자는 다른 사용자의 영업 건을 해제할 수 없다.

### 4.4 저장 방식
- 1차 구현: 서버 프로세스 메모리 저장
- 2차 구현: Supabase/Postgres 영속 저장

## 5. 사용자 화면 요구사항

### 5.1 대상 화면
- 대상은 사용자 모드의 `프로젝트 현황` 카드형 리스트다.
- 현재 카드에는 아래와 같은 줄이 있다.
  - 연면적 / 공사비
  - 빌딩자동제어 추정금액
  - 설계사무소 / 착공
  - 개찰예정일
  - 담당 / 현장
- `영업현황` 줄은 `담당 / 현장` 줄 바로 아래에 추가한다.

### 5.2 카드 내 표시 항목
각 프로젝트 카드에는 아래 항목이 추가된다.

1. `영업` 버튼
2. 현재 담당자 표시
3. 영업 시작 시각 표시
4. `영업현황` 입력칸
5. 해제 버튼

### 5.3 상태별 동작

#### 상태 A: 아직 아무도 영업 시작 안 함
- `영업` 버튼 활성화
- `영업현황` 입력칸 비활성화 또는 read-only
- 담당자/시작 시각 미표시

#### 상태 B: 내가 영업 담당자
- `영업중` 상태 배지 표시
- `영업현황` 입력칸 활성화
- 저장 버튼 활성화
- `해제` 버튼 표시

#### 상태 C: 다른 사용자가 영업 담당자
- `이미 OOO이 진행 중` 표시
- `영업` 버튼 비활성화
- `영업현황`은 읽기 전용으로 표시
- 일반 사용자에게는 `해제` 버튼 비표시
- 관리자 모드에서는 `강제 해제` 버튼 표시 가능

### 5.4 기록 시점
- 사용자가 `영업` 버튼을 누르고 성공하면 아래 값이 즉시 기록된다.
  - `owner_user_id`
  - `owner_email`
  - `owner_display_name`
  - `claimed_at`

### 5.5 영업현황 입력
- `영업현황`은 자유 입력 텍스트다.
- 초기 UI는 `textarea`를 사용한다.
- 저장은 `저장 버튼` 클릭 또는 `Ctrl+Enter`로 처리할 수 있다.
- 저장 권한은 `영업 담당자 본인`에게만 있다.

## 6. 관리자 화면 요구사항

### 6.1 집계 목적
- 관리자 페이지에서 “누가 어떤 영업을 진행 중인지”를 사람 기준으로 파악할 수 있어야 한다.

### 6.2 관리자 집계 패널
관리자 모드에 `영업사원별 진행 프로젝트` 패널을 추가한다.

표시 형태 예시:

```text
1번 영업사원
1. xxx 프로젝트 | 1.0~1.5억원 추정 | 2025-01-01 영업 시작 | 영업 79일차
2. yyy 프로젝트 | 0.5~0.8억원 추정 | 2025-05-01 영업 시작 | 영업 12일차
3. ddd 프로젝트 | 2.3~2.8억원 추정 | 2026-02-01 영업 시작 | 영업 48일차
총 추정금액: 3.8~5.1억원
```

### 6.3 관리자 집계 항목
영업사원별로 아래를 보여준다.
- 영업사원 이름
- 담당 프로젝트 수
- 각 프로젝트명
- 프로젝트별 추정 금액
- 프로젝트별 영업 시작일
- 프로젝트별 경과일
- 해당 영업사원이 맡고 있는 프로젝트 총 추정금액

### 6.4 경과일 계산
- `경과일 = 현재 시각 - claimed_at`
- 단위는 기본적으로 `일(day)`로 표기한다.
- 필요 시 `N일차` 형식으로 표기한다.

## 7. 추정 금액 계산 규칙

### 7.1 원본 필드
- 우선 사용 필드는 기존 프로젝트/트래커에 이미 있는 `building_automation_estimated_amount`다.

### 7.2 표시 규칙
- 원본 문자열은 그대로 카드/관리자 패널에 표시한다.
- 예:
  - `1.0~1.5억원 추정`
  - `0.5~0.8억원 추정`
  - `2.3억원 추정`

### 7.3 합산 규칙
- 관리자 총 추정금액은 `low_amount_krw`, `high_amount_krw`를 별도 숫자로 파싱해서 합산한다.
- 예:
  - `1.0~1.5억원` -> `low=100,000,000`, `high=150,000,000`
  - `2.3억원` -> `low=230,000,000`, `high=230,000,000`
- 파싱 실패 시:
  - 문자열은 그대로 보여준다.
  - 총합 계산에서는 제외한다.
  - 필요하면 `합산 제외 n건`을 함께 표시한다.

## 8. 데이터 모델

### 8.1 1차 `in-memory` 도메인 모델

```python
sales_claim = {
    "organization_id": "...",
    "project_id": "...",
    "source_entry_id": "...",
    "source_run_id": "...",
    "project_name": "...",
    "owner_user_id": "...",
    "owner_email": "...",
    "owner_display_name": "...",
    "claimed_at": "...",
    "released_at": None,
    "is_active": True,
    "sales_note": "...",
    "sales_note_updated_at": "...",
    "sales_note_updated_by": "...",
    "estimated_amount_text": "...",
    "estimated_amount_low_krw": 0,
    "estimated_amount_high_krw": 0,
}
```

### 8.2 1차 저장소 구조
- 메모리 저장소는 `project_id` 기준 맵을 사용한다.

예:

```python
ACTIVE_SALES_CLAIMS = {
    "<project_id>": sales_claim,
}
```

- 동시 요청 충돌을 막기 위해 `threading.Lock` 또는 저장소 레벨 lock을 둔다.

## 9. 향후 DB 영속화 스키마

### 9.1 현재 상태 테이블
추천 테이블명: `project_sales_claims`

```sql
create table public.project_sales_claims (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.organizations(id) on delete cascade,
  project_id uuid not null,
  source_entry_id uuid references public.tracker_entries(id) on delete set null,
  source_run_id uuid references public.pipeline_runs(id) on delete set null,
  project_name text not null default '',
  owner_user_id uuid not null references public.users(id) on delete restrict,
  owner_email text not null default '',
  owner_display_name text not null default '',
  claimed_at timestamptz not null default now(),
  released_at timestamptz,
  is_active boolean not null default true,
  sales_note text not null default '',
  sales_note_updated_at timestamptz,
  sales_note_updated_by uuid references public.users(id) on delete set null,
  estimated_amount_text text not null default '',
  estimated_amount_low_krw bigint,
  estimated_amount_high_krw bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index ux_project_sales_claims_active_project
  on public.project_sales_claims (organization_id, project_id)
  where is_active = true;
```

### 9.2 이벤트/감사 로그 테이블
추천 테이블명: `project_sales_claim_events`

```sql
create table public.project_sales_claim_events (
  id bigint generated always as identity primary key,
  organization_id uuid not null references public.organizations(id) on delete cascade,
  claim_id uuid not null references public.project_sales_claims(id) on delete cascade,
  project_id uuid not null,
  actor_user_id uuid references public.users(id) on delete set null,
  actor_email text not null default '',
  actor_display_name text not null default '',
  event_type text not null,
  old_value_json jsonb not null default '{}'::jsonb,
  new_value_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  constraint project_sales_claim_events_type_check
    check (event_type in ('claim', 'release', 'force_release', 'note_update'))
);
```

### 9.3 DB 설계 의도
- `project_sales_claims`: 현재 활성 상태
- `project_sales_claim_events`: 이력/감사 로그
- 영속화 2차 구현 시에는 메모리 저장소를 이 테이블 구현으로 교체한다.

## 10. API 계약

### 10.1 영업 시작
`POST /api/sales-claims/projects/{project_id}/claim`

요청:

```json
{
  "source_entry_id": "uuid",
  "source_run_id": "uuid",
  "project_name": "xxx 프로젝트",
  "estimated_amount_text": "1.0~1.5억원 추정"
}
```

응답:

```json
{
  "changed": true,
  "claim": {
    "project_id": "uuid",
    "owner_user_id": "uuid",
    "owner_email": "user1@example.com",
    "owner_display_name": "1번 영업사원",
    "claimed_at": "2026-03-20T12:34:56Z",
    "is_active": true,
    "sales_note": ""
  }
}
```

오류:
- `409 conflict`: 이미 다른 사용자가 영업 중

### 10.2 영업현황 저장
`PATCH /api/sales-claims/projects/{project_id}`

요청:

```json
{
  "sales_note": "발주처 1차 통화 완료. 다음 주 미팅 예정."
}
```

권한:
- 영업 담당자 본인만 가능

### 10.3 영업 해제
`POST /api/sales-claims/projects/{project_id}/release`

요청:

```json
{
  "force": false
}
```

권한:
- `force=false`: 본인만 가능
- `force=true`: 관리자만 가능

### 10.4 프로젝트별 현재 영업 상태 조회
`GET /api/sales-claims`

용도:
- 사용자 카드/보드에 현재 담당자와 상태를 합쳐서 보여주기

### 10.5 영업사원별 관리자 집계
`GET /api/sales-claims/summary-by-user`

응답 예시:

```json
{
  "items": [
    {
      "user_id": "uuid",
      "user_name": "1번 영업사원",
      "user_email": "1@example.com",
      "active_project_count": 3,
      "total_low_krw": 380000000,
      "total_high_krw": 510000000,
      "projects": [
        {
          "project_id": "uuid",
          "project_name": "xxx 프로젝트",
          "estimated_amount_text": "1.0~1.5억원 추정",
          "claimed_at": "2025-01-01T00:00:00Z",
          "elapsed_days": 79
        }
      ]
    }
  ]
}
```

## 11. 권한 규칙

### 11.1 `org_user`
- 프로젝트 카드 조회 가능
- 비어 있는 프로젝트에 대해 `영업` 시작 가능
- 본인이 담당자인 프로젝트의 `영업현황` 수정 가능
- 본인이 담당자인 프로젝트 해제 가능
- 다른 사용자의 프로젝트는 수정/해제 불가

### 11.2 `org_admin`
- 위 모든 기능 가능
- 다른 사용자의 프로젝트 강제 해제 가능
- 관리자 집계 패널 조회 가능

### 11.3 `platform_admin`
- 모든 조직의 영업 점유/집계 접근 가능
- 초기 구현에서는 최소한 `org_admin`과 같은 강제 해제/조회 권한을 가진다

## 12. 동시성 규칙
- 같은 `project_id`에 대해 두 사용자가 거의 동시에 `영업`을 누를 수 있다.
- 이 경우 저장소 레벨에서 원자적으로 검사해야 한다.

규칙:
1. `project_id`에 활성 claim이 없으면 생성
2. 이미 활성 claim이 있으면 `409 conflict`
3. 프론트는 `이미 OOO이 영업 중` 메시지 표시

## 13. 화면 배치 상세

### 13.1 사용자 카드
현재 카드 줄 구성:
- 설계사무소 / 착공
- 개찰예정일
- 담당 / 현장

변경 후:
- 설계사무소 / 착공
- 개찰예정일
- 담당 / 현장
- `영업상태 / 영업시작`
- `영업현황`
- `영업 / 해제 / 저장` 버튼 줄

### 13.2 영업상태 표시 예시
- `영업 가능`
- `1번 영업사원 진행 중`
- `내가 진행 중`
- `2026-03-20 09:15 시작`

## 14. 관리자 집계 UX 상세
- 기본 정렬: 영업사원 이름순 또는 현재 담당 프로젝트 수 내림차순
- 각 영업사원 카드/섹션에 아래 표시
  - 이름
  - 담당 프로젝트 수
  - 총 추정금액
  - 프로젝트별 리스트
- 프로젝트별 리스트에는 아래 표시
  - 프로젝트명
  - 추정 금액
  - 영업 시작일
  - 경과일
  - 현재 영업현황 메모 요약

## 15. 1차 구현 수용 기준
1. 사용자 `1`이 프로젝트 A를 영업 시작하면 사용자 `2`, `3`은 같은 프로젝트 A에 대해 `영업` 버튼을 누를 수 없다.
2. 사용자 `2`, `3`에게는 이미 누가 진행 중인지 표시된다.
3. 사용자 `1`은 프로젝트 A 카드에서 `영업현황`을 입력/저장할 수 있다.
4. 저장된 영업현황은 같은 서버 세션 동안 다른 사용자에게 즉시 보인다.
5. 사용자 `1` 또는 관리자만 프로젝트 A를 해제할 수 있다.
6. 관리자 모드에서 영업사원별 프로젝트 분류와 총 추정금액이 보인다.
7. 서버 재시작 시 in-memory 데이터는 사라진다.
8. 이후 DB 저장소로 전환해도 API/화면 계약은 유지된다.

## 16. 구현 순서 권장안
1. 테스트용 사용자 3명 로그인 가능 상태 준비
2. in-memory `sales claim` 저장소 구현
3. 프로젝트 카드에 `영업` / `해제` / `영업현황` UI 추가
4. `project_id` 기준 잠금 구현
5. 관리자 집계 패널 추가
6. DB 테이블 마이그레이션 추가
7. in-memory -> Supabase/Postgres 저장소 교체

## 17. 주의사항
- 현재 1차는 `빠른 검증용`이다.
- 영업 점유는 업무상 중요한 상태이므로 최종 운영 단계에서는 반드시 DB 영속 저장 + 이벤트 로그가 필요하다.
- `entry_id` 잠금으로 구현하면 동일 프로젝트 중복 담당 문제가 생기므로 금지한다.


## 18. ?? ?? ??

### 18.1 ??? ???? ??? ??
- ?? ?? ??? ??? ??? `??(transfer)`?? ????.
- ?? ? ?? ??? ??? ?? ??? ???.
- ? ???? ?? ????? ???? ?? `????` ???? ?? ????.
- ??? ?? ??:
  - `[2026-03-21 10:30] [???] ??? -> ??? ??`

### 18.2 ??? ??? hard delete ?? ????
- ??/??/?? ??? `users.status`? `inactive` ?? `deactivated`? ?? ????.
- ??? ??? ??? ??? ?? ??? ?? API ??? ????.
- ???? ??? ?? ???? ?? `?? ? ??(active claim)`? 0???? ??.
- ?? ? ??? ?? ??? ?? `??` ?? `??`? ?? ??.
- bootstrap `platform_admin` ??? ???? ???? ????.

### 18.3 ?? ?? ??
- ?? ??? `??`? ??? ????.
- ???:
  - `active`: ?? ?
  - `won`: ?? ??
  - `lost`: ?? ??
- ??? ?? ??:
  - `?? ??`
  - `?? ??`
- ?? ? ??? ??? ???.
  - `[2026-03-21 15:05] [???] ?? ?? ??`
  - `[2026-03-21 16:40] [???] ?? ?? ??`
- ??? ??? `????? ?? ??` ????? ????.

### 18.4 ?? ?? ?? ??
- `claimed_at`? ????? ?? ?? ?? ????.
- `current_owner_assigned_at`? ?? ???? ???? ????.
- ??? ????? ?? ???? ????.
  - `?? ?? 2026-03-01`
  - `?? ?? ?? 2026-03-21`
  - `?? ?? 3??`

