# Phase 2 영업 액션 최소 모델

## 목적
이 문서는 tracker / project 데이터를 `영업 운영`까지 연결하기 위한 최소 액션 모델을 정의한다.

목표는 복잡한 CRM을 바로 만드는 것이 아니라, 프로젝트별로 아래 6가지를 저장할 수 있게 하는 것이다.
1. `owner`
2. `priority`
3. `next_action`
4. `due_date`
5. `status`
6. `memo`

## 설계 원칙
1. 새 모델은 기존 `sales claim` 흐름을 버리지 않고 그 위에 얹는다.
2. `project_id` 단위 저장을 유지한다.
3. claim 잠금 상태와 영업 진행 상태는 분리한다.
4. 최소 모델은 영업팀이 “다음에 누가 무엇을 해야 하는지”를 기록하는 데 집중한다.

## 현재 기반
기존 Phase 2 논의에는 이미 아래가 있다.
1. `project_sales_claims`
2. `project_sales_claim_events`
3. `owner`
4. `sales_note`
5. claim / release / note_update 이벤트

따라서 최소 액션 모델은 새 테이블을 급히 추가하기보다,
우선 `project_sales_claims`를 확장하는 방향이 가장 작고 안전하다.

## 최소 영업 액션 필드

### 1. owner
- 기존 claim owner를 그대로 사용한다.
- 권장 저장 컬럼:
  - `owner_user_id`
  - `owner_email`

### 2. memo
- 기존 `sales_note`를 그대로 메모 필드로 사용한다.
- 사용자 라벨은 `메모` 또는 `영업 메모`로 노출할 수 있다.

### 3. priority
- 새 필드
- 권장 컬럼명: `sales_priority`
- 권장 값:
  - `low`
  - `normal`
  - `high`
  - `urgent`

### 4. next_action
- 새 필드
- 권장 컬럼명: `next_action`
- 예:
  - `발주처 유선 확인`
  - `설계사무소 접촉`
  - `후속 공고 대기`

### 5. due_date
- 새 필드
- 권장 컬럼명: `due_date`
- 의미:
  - 다음 액션 목표일
  - 계약일/개찰일 같은 source field와 분리된 사용자 업무 일정

### 6. status
- 새 필드
- claim lifecycle과 구분하기 위해 권장 컬럼명은 `sales_status`
- 권장 값:
  - `new`
  - `working`
  - `waiting`
  - `blocked`
  - `done`
  - `dropped`

## 왜 claim lifecycle과 분리하나
`claimed_at / released_at`는 “누가 점유하고 있는가”를 뜻한다.
반면 `sales_status`는 “영업 진행 상태가 어디까지 왔는가”를 뜻한다.

예:
1. `claimed_at` 있음 + `sales_status = working`
2. `claimed_at` 있음 + `sales_status = waiting`
3. `released_at` 있음 + `sales_status = done`

즉 둘은 목적이 다르므로 한 필드로 합치지 않는다.

## 권장 스키마 방향
최소 버전은 `project_sales_claims`에 아래 컬럼을 추가한다.
1. `sales_priority text not null default 'normal'`
2. `next_action text not null default ''`
3. `due_date date`
4. `sales_status text not null default 'new'`

`sales_note`는 기존 컬럼을 재사용한다.

## 권장 이벤트 로그 확장
`project_sales_claim_events`에는 아래 이벤트 타입을 추가할 수 있다.
1. `priority_update`
2. `next_action_update`
3. `due_date_update`
4. `status_update`

## 최소 API 방향
최소 API는 기존 claim 응답에 아래 필드를 포함하는 정도로 시작한다.
1. `owner`
2. `sales_note`
3. `sales_priority`
4. `next_action`
5. `due_date`
6. `sales_status`

권장 최소 엔드포인트:
1. `GET /api/projects/{project_id}/sales-action`
2. `PATCH /api/projects/{project_id}/sales-action`

## 화면 최소 요구사항
프로젝트 카드 또는 프로젝트 상세에서 아래를 볼 수 있어야 한다.
1. owner
2. priority
3. next_action
4. due_date
5. status
6. memo

관리자/팀장은 아래도 필요하다.
1. 담당자별 필터
2. due date overdue 필터
3. status별 집계

## 범위 제외
이번 최소 모델에는 아래를 포함하지 않는다.
1. 다단계 approval
2. CRM 파이프라인 전체
3. 고객사/리드/접촉 이력 상세 엔터티
4. 자동 알림 엔진

즉 이번 단계는 `영업 운영보드`의 최소 뼈대만 만든다.
