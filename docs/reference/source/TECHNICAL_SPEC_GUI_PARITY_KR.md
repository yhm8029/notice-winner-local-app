# Phase 1 상세 기술 명세서 (GUI 동등 구현 기준)

- 문서 역할: 기술명세 원천 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: GUI parity 구현을 위해 어떤 내부 기술 규칙과 데이터 흐름을 따라야 하는가
- 상위 기준 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)
- 충돌 시 우선 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)

## 문서 목적
- 이 문서는 Phase 1을 GUI와 기능 동등하게 구현하기 위한 내부 기술 기준을 정의한다.
- 기능명세서가 "무엇을 제공해야 하는가"를 다룬다면, 이 문서는 "그 기능을 어떤 데이터 흐름과 알고리즘으로 맞출 것인가"를 다룬다.

## 문서 경계
이 문서에 포함:
1. `project_tracker`와 `tracker_export`의 내부 실행 모델
2. 외부 데이터 소스와 fallback 순서
3. `run_post_collect`, tracker export 후처리, tracker 기본값 병합 규칙
4. GUI parity를 위해 유지해야 하는 구현 제약

이 문서에서 제외:
1. 화면 배치와 버튼 위치
2. dashboard, report UI, 사용자/관리자 모드 같은 운영 편의 기능
3. 다중 사용자 인증/권한 설계

계약 문서 역할 분리:
- API 계약: [../contracts/api-spec.md](../contracts/api-spec.md)
- DB 계약: [../contracts/db-schema.md](../contracts/db-schema.md)
- 상태 계약: [../contracts/job-lifecycle.md](../contracts/job-lifecycle.md)
- GUI 기준 상세 참고: [APP_REBUILD_SPEC_KR.md](./APP_REBUILD_SPEC_KR.md)

## Phase 정의
- Phase 1: GUI와 기능 및 결과가 동일해야 한다.
- Phase 2: Phase 1 기능을 여러 사용자가 함께 쓰는 구조를 추가한다.

## 핵심 원칙
1. Phase 1의 기술 기준은 "웹만으로 GUI와 같은 결과를 만든다"이다.
2. 외부 API 순서, parser, fallback, rescue는 GUI 기준을 바꾸지 않는다.
3. 운영 편의 기능이 추가되더라도, 핵심 데이터 흐름과 결과 계약을 깨면 안 된다.
4. GUI parity가 필요한 기능과 운영 UX 고도화는 문서를 분리한다.

## 1. 실행 모델

### 1.1 부모 run: `project_tracker`
부모 run은 아래 단계로 진행한다.
1. `collect`
2. `filter`
3. `rescan`
4. `export`
5. `finalize`

역할:
- `collect`: seed 후보 수집
- `filter`: 제목/기관 조건과 프로젝트 후보 정제
- `rescan`: 내부 페이지와 첨부문서 재탐색
- `export`: winner/contract 결과 CSV 생성
- `finalize`: 요약, artifact 등록, 종료 처리

### 1.2 child run: `tracker_export`
트래커 엑셀은 부모 run 내부 단계가 아니라 별도 child run으로 다룬다.

단계:
1. `tracker_export`
2. `finalize`

규칙:
1. child run은 `parent_run_id`로 부모 `project_tracker` run을 참조한다.
2. child run 실패가 부모 run 상태를 다시 바꾸지 않는다.
3. child run은 tracker XLSX 생성과 `tracker_entries` upsert를 함께 처리한다.

### 1.3 수동/자동 실행의 문서 경계
Phase 1 기술 기준의 본질은 "`tracker_export`가 독립 child run으로 유지된다"는 점이다.

다음은 핵심 기술 기준이 아니다.
1. 사용자가 버튼으로 child run을 만들지
2. 운영 편의로 부모 성공 직후 child run을 자동 생성할지

위와 같은 트리거 방식은 운영/사용자 편의 문서에서 다루되, child run 분리 모델 자체는 유지해야 한다.

## 2. 입력과 validation 기준
입력 필드는 GUI와 같은 범위를 따른다.
1. `start_date`
2. `end_date`
3. `contract_date_hint`
4. `bid_no`
5. `notice_title`
6. `demand_org`
7. `rows_per_page`
8. `max_pages`
9. `api_scope`

validation 기준:
1. `bid_no`, `notice_title`, `demand_org` 중 최소 1개 필요
2. 날짜는 `YYYYMMDD`
3. `rows_per_page >= 1`
4. `max_pages >= 1`
5. validation error는 run 생성 전에 차단

## 3. 단계별 기술 기준

### 3.1 collect
collect 단계는 GUI seed 수집과 같은 의미를 가져야 한다.

요구사항:
1. `data.go.kr` 공고 API를 기본 소스로 사용한다.
2. `bid_no`가 있으면 direct lookup을 우선한다.
3. `notice_title`, `demand_org` 필터를 GUI와 같은 방향으로 적용한다.
4. quota 초과, zero-hit, 형식 문제는 GUI와 같은 보조 경로를 따라간다.
5. JSON이 비면 XML fallback을 시도한다.

보조 경로:
1. query-based seed fallback
2. broad/local title fallback
3. zero-hit retry

### 3.2 filter
filter 단계는 GUI의 프로젝트 후보 정리 규칙과 같아야 한다.

요구사항:
1. 공고 제목 정규화 규칙을 GUI와 맞춘다.
2. 기관명/프로젝트명 기준 노이즈 제거를 동일하게 적용한다.
3. 중복 제거 기준을 GUI와 맞춘다.

### 3.3 rescan
rescan 단계는 내부 페이지와 첨부문서를 다시 읽어 winner/contract 탐색에 필요한 raw를 확보하는 단계다.

요구사항:
1. 내부 페이지 재탐색 순서가 GUI와 같아야 한다.
2. 첨부문서 raw 확보 규칙을 GUI와 맞춘다.
3. 로그에 재탐색 히트/미스와 fallback을 남긴다.

### 3.4 export (`run_post_collect`)
export 단계의 핵심 기준은 GUI `run_post_collect` 블랙박스 동등 구현이다.

필수:
1. 입력 CSV와 출력 CSV의 의미가 GUI와 같아야 한다.
2. `winner_name`, `contract_name`, `contract_date`, `contract_amount`, `source_type`, `reason_code`, `evidence_source`의 의미가 같아야 한다.
3. 외부 API 순서를 임의로 바꾸지 않는다.

#### 계약/낙찰 정보 소스 순서
공통 우선:
1. `G2B` 계약 API

교육기관:
1. `G2B`
2. `EAIS`
3. 교육청 웹

일반기관:
1. `G2B`
2. `LOFIN`
3. `EAIS`
4. `HUB`

보조 규칙:
1. `LOFIN`은 일 단위 descending sweep 규칙을 유지한다.
2. `EAIS`, `LOFIN`, `HUB`, 교육청 웹의 fallback 순서를 임의로 뒤집지 않는다.
3. `reason_code`, `source_type`는 실제 채택된 소스를 반영해야 한다.

## 4. tracker export 기술 기준
tracker export의 기준은 GUI `run_tracker_export_script`와 `export_project_tracker_from_winner_csv.py` 동등 구현이다.

필수:
1. `winner_csv`, seed raw, notice raw를 함께 사용한다.
2. 행 단위 처리 기준은 GUI `_prepare_one` 규칙과 같아야 한다.
3. GUI가 쓰는 기본값 병합 규칙을 같은 의미로 재현해야 한다.
4. rescue/recheck가 필요한 경우 GUI와 같은 후처리 순서를 유지한다.

### 4.1 기존 tracker 기본값 병합
GUI parity 기준에서는 기존 tracker workbook 기본값 병합을 구현 범위에 포함한다.

의미:
1. 현재 추출값이 비거나 약할 때 기존 tracker 값이 기본값으로 작동할 수 있다.
2. 웹 구현이 이 병합을 생략하면 GUI와 결과가 달라질 수 있다.

### 4.2 핵심 필드
아래 필드는 GUI 결과와 같은 수준으로 채워져야 한다.
1. `gross_area_scale`
2. `construction_cost`
3. `demand_org_name`
4. `demand_contact`
5. `client_location`
6. `site_location_1`
7. `site_location_2`
8. `architect_office`
9. `construction_start_date`
10. `last_checked_date`
11. `progress_note`
12. `notice_date`
13. `building_automation_estimated_amount`

`architect_office` 추가 규칙:
1. 일반 `native_web` 공고문/첨부 본문에서는 채우지 않는다.
2. `architect_office`는 계약 소스(`LOFIN`, `EAIS`, `G2B 계약`) 또는 명시적 결과 공고에서만 채운다.
3. 초기 공모 공고문/자격요건 본문의 `건축사사무소`, `당선자`, `선정업체` 라벨은 설계사무소 근거로 사용하지 않는다.

### 4.3 금지 사항
다음은 GUI parity 기준에서 허용하지 않는다.
1. placeholder를 실제 결과처럼 저장하는 것
2. source/fallback 순서를 임의로 단순화하는 것
3. GUI가 쓰는 기본값 병합이나 rescue를 근거 없이 제거하는 것
4. 일반 `native_web` 공고문/첨부 라벨을 `architect_office` fallback source로 되살리는 것

## 5. API/DB 계약과의 연결
이 문서가 정의하는 기술 기준은 아래 계약 문서에 반영되어야 한다.
1. `project_tracker` / `tracker_export` run_type
2. `parent_run_id`
3. `progress_stage`
4. `winner_csv`, `tracking_excel` artifact
5. `tracker_entries`, `tracker_entry_audit_logs`

세부 payload와 스키마는 아래 문서를 기준으로 한다.
1. [../contracts/api-spec.md](../contracts/api-spec.md)
2. [../contracts/db-schema.md](../contracts/db-schema.md)
3. [../contracts/job-lifecycle.md](../contracts/job-lifecycle.md)

## 6. GUI parity 완료 기준
상세 기술 기준에서 Phase 1 완료로 보려면 아래를 충족해야 한다.
1. 같은 입력에서 collect/filter/rescan/export 결과가 GUI와 동등하다.
2. `winner_csv` 주요 열이 GUI와 동등하다.
3. `tracking_excel` 핵심 필드와 후처리 결과가 GUI와 동등하다.
4. `LOFIN`, `EAIS`, `HUB`, 교육청 웹 fallback 순서가 GUI 기준과 어긋나지 않는다.
5. 기존 tracker 기본값 병합을 포함한 tracker export 후처리가 GUI와 동등하다.

## 7. 운영 편의 기능과의 경계
다음은 이 문서의 핵심 완성 기준이 아니다.
1. 사용자/관리자 모드
2. dashboard
3. parity report UI
4. panel modularization
5. 부모 성공 후 child 자동 생성 같은 운영 편의 트리거

위 항목은 [../operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md](../operations/OPERATIONS_USER_CONVENIENCE_SPEC_KR.md)에서 다룬다.

