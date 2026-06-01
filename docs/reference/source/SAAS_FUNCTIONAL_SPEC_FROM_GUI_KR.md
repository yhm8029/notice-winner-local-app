# Phase 1 기능 명세서 (GUI 동등 기능 기준)

- 문서 역할: 기능명세 원천 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: GUI parity 기준에서 Phase 1 기능이 무엇이어야 하는가
- 상위 기준 문서: [02_FUNCTIONAL_SPEC_KR.md](../../spec/FUNCTIONAL_SPEC_KR.md)
- 충돌 시 우선 문서: [02_FUNCTIONAL_SPEC_KR.md](../../spec/FUNCTIONAL_SPEC_KR.md)

## 문서 목적
- 이 문서는 웹 제품이 사용자와 운영자에게 어떤 기능을 제공해야 하는지 정의한다.
- Phase 1 완료 기준은 "웹이 현재 GUI와 같은 기능을 수행할 수 있는가"이다.
- 내부 알고리즘, 외부 API 순서, DB/API 계약은 별도 상세 기술 명세서와 계약 문서로 분리한다.

## 문서 경계
이 문서에 포함:
1. 사용자가 화면에서 해야 하는 입력과 확인 동작
2. 실행 시작, 취소, 결과 확인, 파일 다운로드 같은 기능 요구사항
3. GUI와 같은 수준으로 결과가 나와야 한다는 완료 기준

이 문서에서 제외:
1. `LOFIN`, `EAIS`, `HUB`, `교육청 웹` 조회 순서
2. parser, fallback, rescue, `_prepare_one`, `run_post_collect` 같은 내부 구현 규칙
3. DB 컬럼, API payload, child run 생성 방식의 세부 계약
4. 사용자/관리자 모드, dashboard, parity report, panel modularization 같은 운영 편의 기능
5. 인증, 권한, 다중 사용자 협업

참고 문서:
- [TECHNICAL_SPEC_GUI_PARITY_KR.md](./TECHNICAL_SPEC_GUI_PARITY_KR.md)
- [../contracts/api-spec.md](../contracts/api-spec.md)
- [../contracts/db-schema.md](../contracts/db-schema.md)
- [../contracts/job-lifecycle.md](../contracts/job-lifecycle.md)
- [../../TRACKER_QUALITY_BACKFILL_DESIGN_KR.md](../../TRACKER_QUALITY_BACKFILL_DESIGN_KR.md)
- [../../PROJECT_GROUPING_QUALITY_KR.md](../../PROJECT_GROUPING_QUALITY_KR.md)
- [../../PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md](../../PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md)
- [../../PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md](../../PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md)

## 운영형 품질관리 확장 요구사항
이 제품은 단발성 공고 요약기가 아니라 tracker를 누적 관리하는 운영형 시스템이므로, GUI parity 이후에도 아래 요구사항을 유지해야 한다.

### 필드 provenance
트래커 핵심 필드는 값만 보여주지 않고, 각 필드별로 아래 정보를 함께 제공해야 한다.
1. 현재 표시값
2. source key
3. source type
4. reason code
5. evidence preview
6. confidence
7. missing reason
8. 수동 override 여부

적용 대상 최소 필드:
1. `gross_area_scale`
2. `construction_cost`
3. `demand_contact`
4. `architect_office`

### 누락/오염 분류
필드가 비어 있거나 이상값일 때는 단순 빈칸이 아니라 아래 유형으로 분류할 수 있어야 한다.
1. `정상 빈값`
2. `source 없음`
3. `query miss`
4. `구버전 run`

### backfill 운영 절차
규칙 개선 후 과거 tracker row를 다시 보정할 수 있어야 한다.
단, 기존 정상값을 깨뜨리면 안 되므로 아래 순서를 따른다.
1. `dry-run`
2. `overwrite 정책 검토`
3. `실행`

`dry-run` 결과에는 최소 아래가 포함돼야 한다.
1. 현재값
2. 후보값
3. 변경 여부
4. action
5. apply mode
6. 검토 필요 여부

### backfill 정책
자동 반영 가능한 케이스와 검토가 필요한 케이스를 분리해야 한다.

자동 반영 가능:
1. blank -> nonblank
2. 공사비 기반 `building_automation_estimated_amount` 파생
3. 현재값이 명백한 이상값일 때의 안전 교체

자동 반영 금지:
1. nonblank -> 다른 nonblank 충돌
2. 착공 표시값 충돌
3. 근거 source가 약한 값

### 일정 필드 분리 저장
`construction_start_date`는 표시용 필드이고, 내부 운영은 아래 source 필드를 분리 저장해야 한다.
1. `contract_date`
2. `construction_duration_days`
3. `completion_expected_date_explicit`
4. `completion_expected_date_computed`

규칙:
1. explicit 완공예정일과 computed 완공예정일은 분리 저장한다.
2. `building_automation_estimated_amount`는 공사비 기반 파생을 우선한다.
3. schedule split 필드 backfill은 override가 아니라 source 갱신 관점으로 다룬다.

### 프로젝트 grouping 운영 기준
관련 공고 연결과 project grouping 품질은 개별 필드 fill rate와 별도로 관리해야 한다.

운영 규칙:
1. 고정 golden set을 유지한다.
2. grouping 규칙 변경 시 [PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md](./PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md)를 따른다.
3. `pairwise_f1` 하락 또는 과병합 증가는 채택 금지다.
4. 첫 운영 기준선은 `187 row / 141 group` 골든셋을 사용한다.

### Phase 2 최소 영업 액션 모델
Phase 2에서는 tracker / project 데이터를 영업 운영까지 연결하기 위해 최소 액션 필드를 추가한다.

최소 필드:
1. `owner`
2. `priority`
3. `next_action`
4. `due_date`
5. `status`
6. `memo`

설계 원칙:
1. 새 모델은 기존 `sales claim`을 대체하지 않고 확장한다.
2. `memo`는 기존 `sales_note`를 재사용한다.
3. `status`는 claim 점유 상태와 분리된 영업 진행 상태다.
4. 상세 설계는 [PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md](./PHASE2_SALES_ACTION_MINIMUM_MODEL_KR.md)를 따른다.

## Phase 정의
- Phase 1: 현재 GUI와 기능이 동일해야 한다.
- Phase 2: Phase 1에서 맞춘 기능을 여러 사용자가 함께 쓰도록 인증, 권한, 협업 구조를 추가한다.

## Phase 1 운영 전제
1. Phase 1은 1인 내부 운영 기준이다.
2. Phase 1은 로그인 없이 사용할 수 있다.
3. 로컬 GUI 프로그램을 함께 켜지 않아도 웹 저장소만으로 같은 기능을 수행해야 한다.
4. GUI와 다른 운영 편의 기능이 추가되어도, 그것만으로 Phase 1 완료를 선언하지 않는다.

## 포함 범위
1. 검색 조건 입력과 요청 검증
2. `project_tracker` 실행 시작, 상태 확인, 취소
3. 실행 로그와 결과 파일 조회
4. `winner_csv`와 트래커 엑셀 확보
5. 트래커 결과의 웹 확인
6. GUI와 같은 수준의 핵심 필드 채움

## 제외 범위
1. 로그인, 권한, 다중 사용자 충돌 제어
2. dashboard, parity report, report history 같은 검증 보조 화면
3. 사용자/관리자 모드 전환
4. 패널 재배치, 패널 숨김/복원 같은 레이아웃 편의 기능

## 사용자 기능 요구사항

### 1. 검색 조건 입력
사용자는 아래 조건으로 실행 대상을 지정할 수 있어야 한다.
1. `start_date`
2. `end_date`
3. `contract_date_hint`
4. `bid_no`
5. `notice_title`
6. `demand_org`
7. `rows_per_page`
8. `max_pages`
9. `api_scope`

입력 규칙:
1. `bid_no`, `notice_title`, `demand_org` 중 최소 1개는 비어 있지 않아야 한다.
2. 날짜는 `YYYYMMDD` 형식을 사용해야 한다.
3. 페이지 관련 숫자는 1 이상이어야 한다.

### 2. 실행 시작과 취소
1. 사용자는 입력한 조건으로 새 `project_tracker` 실행을 시작할 수 있어야 한다.
2. 사용자는 현재 실행 상태를 확인할 수 있어야 한다.
3. 사용자는 `queued` 또는 `running` 상태의 실행을 취소할 수 있어야 한다.
4. 사용자는 실행 실패 시 실패 원인과 실패 단계 정보를 확인할 수 있어야 한다.

### 3. 실행 결과 확인
사용자는 실행 결과를 웹에서 확인할 수 있어야 한다.

필수 확인 항목:
1. 실행 ID, 상태, 현재 단계
2. 생성 시각, 시작 시각, 종료 시각
3. 로그 목록
4. 산출물 목록
5. 결과 요약

### 4. 결과 파일 확보
Phase 1에서는 아래 결과 파일을 확보할 수 있어야 한다.
1. `winner_csv`
2. `tracking_excel`

그리고 사용자는 아래 동작을 할 수 있어야 한다.
1. `winner_csv` 다운로드
2. `tracking_excel` 다운로드
3. `winner_csv` 미리보기
4. `tracking_excel` 미리보기

주의:
- 트래커 엑셀을 얻는 방식이 버튼이든 자동 생성 보조 기능이든, 기능 요구사항의 본질은 "사용자가 GUI와 같은 트래커 결과를 확보할 수 있어야 한다"이다.

### 5. 트래커 결과 확인
사용자는 웹에서 트래커 결과를 GUI 수준으로 읽고 검토할 수 있어야 한다.

필수:
1. 엑셀 양식 기준 컬럼 표시
2. 주요 필드가 한눈에 보이는 표
3. 행 단위 상세 확인
4. 엑셀 다운로드

### 6. 트래커 데이터 품질
Phase 1은 단순히 파일이 생성되는 것으로 완료되지 않는다.

아래 핵심 컬럼은 원문에 실제로 값이 없는 경우를 제외하면 GUI와 같은 수준으로 채워져야 한다.
1. `연면적/규모`
2. `공사비`
3. `수요기관명`
4. `수요기관(부서 및 담당자)`
5. `발주처 위치`
6. `현장 위치`
7. `설계사무소(건축)`
8. `공사기간(착공일)`
9. `최종 점검일자`
10. `주요진행사항`

금지:
1. placeholder 값으로 결과를 대신하는 것
2. GUI와 다른 임시 문구를 실제 결과처럼 노출하는 것

## 동등성 판단 기준
Phase 1 완료 판단은 아래 3가지를 모두 만족해야 한다.
1. 실행 흐름이 GUI와 동일하다.
2. 산출물이 GUI와 동일하거나 동등하다.
3. 트래커 핵심 필드가 GUI와 같은 수준으로 채워진다.

## 완료 기준
아래를 모두 만족해야 Phase 1 완료로 본다.
1. 같은 입력으로 GUI와 같은 기능 흐름을 끝까지 수행할 수 있다.
2. `winner_csv`와 `tracking_excel`을 웹에서 확보할 수 있다.
3. 트래커 핵심 필드가 GUI와 같은 수준으로 채워진다.
4. 웹에서 결과를 충분히 검토할 수 있다.

아래는 완료 판정 보조 자료일 뿐 단독 기준이 아니다.
1. parity report
2. artifact diff report
3. dashboard 요약 값

