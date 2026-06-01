# Tracker Quality / Backfill 설계 명세

## 문서 목적
- 이 문서는 tracker 품질관리 계층의 설계를 정의한다.
- 대상 범위는 `field provenance`, `missing reason`, `dry-run backfill`, `apply policy`, `schedule split storage`다.
- GUI parity 자체를 바꾸는 문서가 아니라, parity 이후에도 운영형 시스템 품질을 유지하기 위한 설계 문서다.

## 관련 구현 파일
1. `backend/services/tracker_field_provenance.py`
2. `backend/api/app.py`
3. `backend/api/schemas.py`
4. `scripts/dry_run_core_field_backfill.py`
5. `scripts/apply_core_field_backfill.py`

## 배경
현재 시스템은 `project_tracker -> tracker_export -> tracker_entries` 흐름으로 결과를 영속화한다.
문제는 규칙이 좋아져도 과거 live row에 stale 값이 남을 수 있다는 점이다.

따라서 운영 계층에는 다음이 필요하다.
1. 각 필드가 왜 그렇게 채워졌는지 설명하는 provenance
2. 왜 비었는지 설명하는 missing reason
3. 개선 규칙을 과거 row에 안전하게 적용하는 dry-run / apply 정책

## 1. Field Provenance

### 1.1 목표
핵심 tracker 필드는 값만 보여주지 않고 아래 메타데이터를 같이 계산한다.

필수 항목:
1. `current_value`
2. `source_key`
3. `source_label`
4. `source_type`
5. `source_type_label`
6. `reason_code`
7. `source_reason`
8. `evidence_preview`
9. `confidence`
10. `missing_reason_code`
11. `missing_reason`
12. `is_missing`
13. `is_overridden`

### 1.2 최소 적용 필드
1. `architect_office`
2. `gross_area_scale`
3. `construction_cost`
4. `demand_contact`

### 1.3 원칙
1. API 응답과 누락 리포트는 동일한 provenance 분류 함수를 사용한다.
2. 수동 override는 `manual_override` source로 구분한다.
3. `construction_cost`는 원문 raw field가 `notice_construction_cost`여도 tracker 진단 키는 `construction_cost`로 통일한다.
4. `missing_reason`은 단순 빈칸이 아니라 운영자가 바로 이해할 수 있는 설명이어야 한다.

### 1.4 confidence 정책
1. `confirmed_*` source는 기본 `high`
2. `estimated_*` source는 기본 `medium`
3. `fallback_*` source는 기본 `low`
4. `manual_override`는 `manual`
5. expected blank는 `expected_blank`

## 2. Missing Reason

### 2.1 목적
필드가 비어 있을 때 “왜 비었는지”를 코드와 문구로 분리해 남긴다.

### 2.2 기본 분류
1. `정상 빈값`
2. `source 없음`
3. `query miss`
4. `구버전 run`

### 2.3 사용 규칙
1. auxiliary / 평가용역 / 관리용역처럼 특정 필드가 원래 비어도 되는 경우는 `정상 빈값`
2. 허용 source(EAIS/LOFIN/HUB/G2B)에 흔적이 전혀 없으면 `source 없음`
3. source 흔적은 있지만 현재 규칙이 확정에 실패하면 `query miss`
4. winner row에 raw value 흔적이 있는데 tracker effective에 반영이 안 됐으면 `구버전 run`

## 3. Backfill Dry-Run

### 3.1 목적
개선 규칙을 live에 바로 반영하지 않고, 먼저 현재값과 후보값을 비교한다.

### 3.2 dry-run row 필수 컬럼
1. `entry_id`
2. `bid_no`
3. `bid_ord`
4. `project_name`
5. `run_id`
6. `run_lookup_status`
7. `field_name`
8. `current_value`
9. `candidate_value`
10. `changed`
11. `action`
12. `apply_mode`
13. `target_flags`
14. `attachment_note`
15. `synap_note`

### 3.3 action 분류
1. `safe_fill_blank`
2. `safe_schedule_fill`
3. `safe_derive_from_cost`
4. `safe_replace_implausible_current`
5. `review_conflict`
6. `noop`

### 3.4 apply_mode 분류
1. `override`
2. `source_rerun_required`
3. `skip`

## 4. Backfill Apply 정책

### 4.1 자동 반영 가능
1. blank -> nonblank
2. 공사비 기반 `building_automation_estimated_amount` 파생
3. 현재값이 명백한 이상값일 때의 안전 교체

### 4.2 자동 반영 금지
1. nonblank -> 다른 nonblank 충돌
2. `construction_start_date` display 충돌
3. 근거 source가 약한 값

### 4.3 field별 처리
`override` 가능:
1. `gross_area_scale`
2. `construction_cost`
3. `demand_contact`
4. `architect_office`
5. `building_automation_estimated_amount`
6. 기타 기존 `TRACKER_EDITABLE_FIELDS`

`source_rerun_required`:
1. `contract_date`
2. `construction_duration_days`
3. `completion_expected_date_explicit`
4. `completion_expected_date_computed`

### 4.4 실행 순서
1. `dry-run`
2. 정책 검토
3. `override` 가능한 안전 건만 실행
4. `source_rerun_required`는 별도 rerun/backfill 파이프라인에서 처리

## 5. Schedule Split 저장

### 5.1 목적
`construction_start_date` display 필드 하나에 계약일/기간/완공예정일을 섞지 않기 위해 source 필드를 분리 저장한다.

### 5.2 저장 필드
1. `contract_date_source`
2. `construction_duration_days_source`
3. `completion_expected_date_explicit_source`
4. `completion_expected_date_computed_source`

### 5.3 규칙
1. explicit 완공예정일과 computed 완공예정일은 분리 저장한다.
2. computed 완공예정일은 trusted contract source + duration이 있을 때만 계산한다.
3. `construction_start_date`는 display field라서 source split을 바탕으로 조합하되, 충돌 시 자동 overwrite하지 않는다.

## 6. 빌딩자동제어 추정금액

### 6.1 원칙
`building_automation_estimated_amount`는 독립 추출값이 없을 때 `construction_cost` 기반 파생을 우선한다.

### 6.2 기본 계산
1. 공사비의 1%~2%
2. 기존 명시 추출값이 있으면 그 값을 우선
3. 공사비가 blank/비정상이면 파생값도 blank

## 7. 운영 산출물
이 계층은 아래 산출물을 남겨야 한다.
1. dry-run CSV
2. dry-run JSON
3. dry-run summary JSON
4. apply plan CSV
5. apply plan JSON
6. apply/skip 실행 결과 CSV/JSON

## 8. 채택 기준
1. 신규 규칙은 기존 성공률보다 낮아지면 채택 금지
2. baseline vs after 비교를 필드별로 남겨야 한다
3. 기존 정상 케이스를 깨뜨리면 자동 반영 금지
4. `review_conflict`는 검토 큐로 남긴다
