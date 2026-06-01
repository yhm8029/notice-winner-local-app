# 낙찰 파이프라인 GUI 재구현 명세서 (코드 유실 대비)

- 문서 역할: 원천 기준 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 코드 유실 시 원래 GUI 시스템을 어떤 기준으로 재구현해야 하는가
- 상위 기준 문서: [.../../spec/FUNCTIONAL_SPEC_KR.md](.../../spec/FUNCTIONAL_SPEC_KR.md), [.../../spec/SYSTEM_DESIGN_KR.md](.../../spec/SYSTEM_DESIGN_KR.md)
- 충돌 시 우선 문서: [.../../spec/FUNCTIONAL_SPEC_KR.md](.../../spec/FUNCTIONAL_SPEC_KR.md)

작성일: 2026-03-11  
대상 레포: `notice-winner-pipeline-project`

## 1. 목적

이 문서는 코드가 유실되어도 동일 기능의 앱을 다시 만들 수 있도록, 현재 구현의 기능 계약을 모듈 단위로 고정한 명세다.

## 2. 시스템 범위

이 앱은 현재 데스크톱 GUI 기준으로 4단계 파이프라인을 한 프로세스에서 실행한다.

1. 공고 시드 수집 (data.go.kr + 폴백)
2. 낙찰자/계약 정보 수집 (G2B/LOFIN/EAIS/교육청/HUB + 웹 크롤링)
3. 트래커 엑셀 생성/갱신
4. GUI 로그/미리보기/파일 열기/수동 정리 저장

### 2.1 문서 경계

- 이 문서는 Tkinter GUI 현재 구현을 재구현하기 위한 기준이다.
- 웹/SaaS 설계 기준은 `docs/reference/contracts/job-lifecycle.md`, `docs/reference/contracts/api-spec.md`, `docs/reference/contracts/db-schema.md`, `docs/reference/contracts/request-response-examples.md`를 따른다.
- 특히 현재 GUI는 트래커 정리 저장을 같은 프로세스 후처리로 수행하지만, SaaS Phase 1 설계에서는 `POST /api/runs/{run_id}/tracker-export`로 child run을 생성해 분리한다.

핵심 파일:

- 엔트리: `run_gui.py`
- GUI: `app/ui/main_window.py`
- 백엔드 공통 로직: `run_gui_backend.py`
- 낙찰 수집 엔진: `pipeline_post_collect_v1.py`
- 트래커 후처리: `projects/nakchal/scripts/export_project_tracker_from_winner_csv.py`

## 3. 실행 진입점

실행 순서:

1. `run_gui.py` → `app.run_gui.run()`
2. `app/run_gui.py` → `app.ui.main_window.run()`
3. `App(tk.Tk)` 생성 후 메인루프 시작

## 4. 현재 모듈 구조 명세

## 4.1 `app/*` 계층

현재 `app/infra`, `app/domain`, `app/integrations`, `app/services`는 대부분 `run_gui_backend.py`의 함수/상수를 재노출하는 브리지 레이어다.

재구현 시 동등성 조건:

1. 외부에서 `app/*` 경로로 import 가능한 심볼 이름 유지
2. 심볼 의미/입출력 동작은 기존 `run_gui_backend.py`와 동일

## 4.2 `app/ui/main_window.py`

`App` 클래스가 GUI와 실행 제어를 직접 담당한다.

주요 메서드:

- `__init__`
- `_build_ui`
- `_start_run`
- `_stop_run`
- `_run_pipeline_thread`
- `_drain_queue`
- `_append_log`
- `_load_result_table`
- `_export_tracker_workbook`
- `_open_result`

동등성 조건:

1. 입력 필드, 버튼, 로그 박스, 결과 테이블 구조 유지
2. 버튼 상태 전이 유지
3. 큐 이벤트 프로토콜 유지

## 4.3 `run_gui_backend.py`

역할:

1. 환경변수/경로/상수
2. 시드 수집 로직
3. CSV 머지
4. 트래커 엑셀 기본 빌더
5. 외부 후처리 스크립트 실행기

## 5. UI 기능 계약

입력 필드:

1. 시작일 `YYYYMMDD`
2. 종료일 `YYYYMMDD`
3. 계약일 힌트 `YYYYMMDD` (선택)
4. 공고번호 (선택)
5. 공고명 (선택)
6. 수요기관 (선택)
7. 페이지당 건수 (기본 100)
8. 최대 페이지 (기본 3)
9. API 범위 (`공사만`, `용역만`, `물품만`, `전체`)

검증 규칙:

1. 공고번호/공고명/수요기관 중 최소 1개 필수
2. 날짜 형식 8자리 숫자
3. 시작일 <= 종료일
4. 페이지당 건수/최대 페이지는 정수 >= 1
5. G2B 키 없으면 실행 불가

버튼:

1. 파이프라인 실행
2. 중지
3. 결과 CSV 열기
4. 정리해서 저장

큐 이벤트 종류:

- `log`
- `error`
- `stopped`
- `done`
- `tracker_done`
- `export_saved`
- `export_error`
- `export_idle`

`_drain_queue` 처리 계약:

1. `error` 수신 시 상태 `실패`, 버튼 원복, 에러 팝업
2. `done` 수신 시 상태 `완료`, 결과 테이블 최대 500행 로드
3. `stopped` 수신 시 상태 `중지됨`
4. `tracker_done` 수신 시 마지막 트래커 파일 경로 갱신

## 6. 파일/데이터 계약

핵심 경로:

- 시드 입력: `tests/winner_pipeline_seed_input.csv`
- Step3 결과: `output/winner_pipeline_posts_files_v1_1.csv`
- 트래커 기본 출력: `output/프로젝트_트랙커_채움.xlsx`
- 공고 원문 캐시: `output/winner_notice_raw_cache.json`

시드 CSV 헤더:

- `bid_no`
- `bid_ord`
- `project_name`
- `org_name`
- `announce_date`
- `g2b_verified`

`run_post_collect` 입력 CSV 필수 열:

- `bid_no`
- `bid_ord`
- `project_name_norm` 또는 `project_name`
- `org_name`
- `announce_date`
- `g2b_verified`
- `internal_search_url`

`run_post_collect` 출력 CSV 열:

- `bid_no`
- `bid_ord`
- `rank`
- `project_name_norm`
- `g2b_verified`
- `source_type`
- `internal_search_url`
- `post_url`
- `post_title`
- `winner_name`
- `winner_confidence`
- `winner_pattern`
- `post_score`
- `file_url`
- `file_name`
- `confidence_score`
- `reason_code`
- `review_flag`
- `escalate`
- `contract_name`
- `contract_date`
- `contract_amount`
- `evidence_source`
- `parser_version`
- `run_mode`
- `status`
- `hub_check_note`

GUI 머지 출력 기본 열(필드 자동 생성 fallback):

- `bid_no`
- `bid_ord`
- `rank`
- `project_name_norm`
- `g2b_verified`
- `source_type`
- `internal_search_url`
- `post_url`
- `post_title`
- `winner_name`
- `winner_confidence`
- `winner_pattern`
- `post_score`
- `file_url`
- `file_name`
- `confidence_score`
- `reason_code`
- `review_flag`
- `escalate`
- `contract_name`
- `contract_date`
- `contract_amount`
- `evidence_source`
- `parser_version`
- `run_mode`
- `status`

## 7. 단계별 파이프라인 명세

## 7.1 단계 1: 시드 수집 (`fetch_seed_rows`)

입력:

1. 서비스키
2. 날짜범위
3. 공고번호/공고명/수요기관 필터
4. 페이지 설정
5. endpoint mode

처리:

1. 월 단위 범위 분할 조회
2. 공고번호가 있으면 direct-bid 우선 조회
3. 서버 title 필터 1차
4. 실패 시 broad-local-title 2차
5. JSON 비어있으면 XML fallback
6. 필터링 후 중복 제거

쿼터 처리:

1. 엔드포인트별 `429` 추적
2. 모든 시도 엔드포인트가 쿼터 초과면 `AllEndpointsQuotaExceededError`
3. GUI에서 폴백 시드 생성으로 전환

## 7.2 단계 1 폴백: 질의 기반 시드

순서:

1. LOFIN 계약 OpenAPI 제목 검색
2. 실패 시 Google HTML 검색
3. 제목 정규화 + generic 용어 제거 + overlap gate 적용

## 7.3 단계 2: 낙찰/계약 수집 (`run_post_collect`)

입력:

1. `internal_nav_csv`
2. `contract_date_hint`
3. `lofin_api_key`
4. `g2b_service_key`
5. G2B 조회 창

계약 확인 우선순위:

교육기관:

1. G2B 계약 API
2. EAIS API
3. 교육청 계약현황 웹

일반기관:

1. G2B 계약 API
2. LOFIN API
3. EAIS API
4. HUB

고신뢰 계약 히트 시 스킵 규칙:

1. `g2b_contract_api` 매칭점수 >= 0.80이면 게시글 크롤링 생략
2. `lofin_api` 매칭점수 >= 0.80이면 게시글 크롤링 생략
3. `edu_web`/`eais_web` 계약일치면 게시글 크롤링 생략

날짜 창 규칙:

1. `contract_date_hint`가 있으면 해당 값 중심
2. 없으면 공고일 +30일부터 +210일까지
3. 미래일은 `today`로 clamp
4. 교육청 웹은 월 단위 descending 조회
5. LOFIN은 일 단위 descending 힌트 생성

게시글 수집:

1. 기본 `extract_post_candidates`
2. 비어있으면 recovery probe
3. 중복 URL 제거
4. generic 후보 제거
5. 상위 5개 게시글, 첨부 상위 5개 파일까지만 반영

낙찰 추출:

1. `winner_name_extractor(snippet/title/project_name_norm)` 사용
2. 웹 추출 실패 시 계약 API 당선자명으로 보강
3. 점수/도메인으로 `FOUND/REVIEW/CANDIDATE` 결정

## 7.4 단계 3: 트래커 후처리 스크립트

실행 파일:

- `projects/nakchal/scripts/export_project_tracker_from_winner_csv.py`

CLI 인자:

- `--winner-csv`
- `--seed-csv`
- `--template`
- `--out`
- `--notice-json`
- `--g2b-key`
- `--demand-org-filter`
- `--llm-correct`
- `--anthropic-key`
- `--llm-model`
- `--llm-max-rows`

처리:

1. winner CSV에서 `bid_no/bid_ord` 기준 best row 선별
2. seed 맵 결합
3. notice raw cache 조회/미스시 G2B 공고 재조회
4. 건별 `_prepare_one` 병렬 처리 (`TRACKER_ROW_WORKERS`, 기본 4)
5. area/cost/contact/site/winner/progress 계산
6. 다단계 중복 제거
7. 지역별 시트 분리 작성

템플릿 필수 헤더(2행 기준):

1. `NO.`
2. `프로젝트명(시설비)`
3. `연면적/규모`
4. `공사비` 또는 `예정공사비`
5. `수요기관명`
6. `수요기관(부서 및 담당자)`
7. `발주처 위치`
8. `현장 위치`
9. `설계사무소(건축)`
10. `공사기간(착공일)`
11. `최종입찰일자` 또는 `최종점검일자`
12. `주요진행사항`
13. `공고일`
14. `담당자`

## 8. 연락처 추출 명세 (최신)

정책:

1. 계약 API 연락처 직접 채택 금지
2. 공고문 텍스트 기반 추출만 허용

핵심 함수:

1. `_iter_contact_phone_contexts`
2. `_extract_contact_candidates_from_notice_text`
3. `_extract_contact_from_notice_text` (wrapper)
4. `_normalize_contact_candidate`
5. `_is_suspicious_contact_value`

후보 추출:

1. 전화번호 후보 스캔 (`PHONE_FLEX_PAT`)
2. 전화 주변 라인 문맥 추출
3. 부서명 후보를 라인별 수집
4. 앵커 라인(`문의/담당/연락처/☎`) 우선
5. 같은 전화라도 복수 후보 유지

LLM 연계:

1. 후보 2개 이상이면 `contact_needs_llm=True` 강제
2. `_anthropic_extract_notice_fields`에 후보 목록 전달
3. LLM 응답 `contact_selected_idx` 지원
4. 인덱스 유효하면 해당 후보를 우선 채택

의심값 규칙:

1. 비어있는 연락처
2. 노이즈 패턴
3. 조달/계약 전담 부서 패턴 (`입찰`, `계약`, `지방계약법`, `조달`, `회계`)

## 9. 면적/공사비 추출 명세

면적:

1. 강라벨(`총연면적`, `건축연면적`) 우선
2. 약라벨 단독은 보수적으로 제외
3. 범위/층별/대지면적 오탐 방지
4. 건축 프로젝트에서 `<100㎡`는 의심값

공사비:

1. 공사비/총사업비 계열 우선
2. 설계비/평가비/용역비 계열 제외
3. 범위 `100,000,000 <= won <= 5,000,000,000,000`
4. 면적 대비 저비용/고비용 이상치 필터

강제 확인 프로젝트:

특정 키워드 프로젝트는 area/cost를 무조건 `확인필요`로 고정한다.

## 10. LLM 보정 명세

모델:

- 기본 `claude-3-5-haiku-latest`

활성 조건:

1. `--llm-correct` true
2. `ANTHROPIC_API_KEY` 존재
3. 예산 `llm_remaining > 0`

예산:

- 기본 `TRACKER_LLM_MAX_ROWS=20`

입력:

1. `notice_text` 또는 contact 축약 컨텍스트
2. 현재 area/cost/contact
3. `contact_candidates` 목록

출력 스키마:

- `area`
- `cost`
- `contact`
- `contact_selected_idx`
- `evidence_area`
- `evidence_cost`
- `evidence_contact`

## 11. 환경변수 계약

## 11.1 GUI/백엔드

- `DATA_GO_KR_SERVICE_KEY`
- `PUBLIC_DATA_SERVICE_KEY`
- `G2B_SERVICE_KEY`
- `LOFIN_OPENAPI_KEY`
- `LOFIN_API_KEY`
- `LOFIN_KEY`
- `WINNER_PIPELINE_SEED_PARALLEL_WORKERS` (기본 2)
- `WINNER_PIPELINE_SEED_PAGE_WORKERS` (기본 2)

## 11.2 post_collect

- `WINNER_PIPELINE_LOFIN_DATE_SWEEP_WORKERS` (기본 3)
- `WINNER_PIPELINE_LOFIN_GLOBAL_MAX_CONCURRENCY` (기본 4)
- `EAIS_UNTCLSFCD` (기본 1000)

## 11.3 tracker export

- `TRACKER_ROW_WORKERS` (기본 4)
- `TRACKER_LLM_CORRECT` (기본 false)
- `TRACKER_LLM_MAX_ROWS` (기본 20)
- `TRACKER_LLM_MODEL` (기본 `claude-3-5-haiku-latest`)
- `ANTHROPIC_API_KEY`

## 12. 외부 API/사이트 계약

data.go.kr:

1. `BidPublicInfoService/*`
2. `CntrctInfoService/*`

LOFIN:

1. `https://www.lofin365.go.kr/lf/hub/WCEGCF`

EAIS:

1. `AWPAIA01R02` 목록
2. `AWPAIA01R03` 상세
3. `AWPAIA01R05` 참여자

웹:

1. 교육청 계약현황 페이지
2. HUB 설계공모 페이지

## 13. 오류/예외 처리 계약

1. API 429는 엔드포인트 단위 스킵
2. JSON 실패 시 XML fallback 시도
3. 파일 저장 `PermissionError` 시 타임스탬프 파일로 재시도
4. 스레드 예외 발생 시 `stop_event` 세팅 후 중단
5. GUI는 예외를 큐 `error`로 전달하고 팝업 표시

## 14. 성능/동시성 계약

1. 시드 페이지 병렬 조회
2. 시드 건별 post_collect 병렬 실행
3. LOFIN 전역 동시 호출 세마포어 제한
4. 트래커 행 단위 병렬 `_prepare_one`
5. UI 큐 배치 소비 (`80` / 타이핑 시 `12`)

## 15. 재구현 시 동등성 테스트 체크리스트

1. GUI 입력 검증 오류 메시지 동작 동일
2. `20250101~20250228` 같은 기간 실행 시 결과 CSV 생성
3. 쿼터 초과 시 query-based seed fallback 동작
4. post_collect 출력 열/형식 동일
5. 트래커 템플릿 헤더 매핑 동일
6. 연락처 후보 N개 + LLM `contact_selected_idx` 반영 동작
7. `정리해서 저장` 버튼으로 타임스탬프 파일 저장 동작
8. 결과 테이블 500행 미리보기 동작

## 16. 모듈별 책임 요약

`app/ui/main_window.py`:

- UI 조립, 사용자 입력, 스레드 시작/중지, 큐 드레인

`app/services/*`:

- 현재는 브리지
- 목표는 오케스트레이션/서비스 분리

`app/integrations/*`:

- 현재는 브리지
- 목표는 API I/O 독립 모듈

`app/domain/*`:

- 현재는 브리지 + 최소 dataclass
- 목표는 텍스트 정규화/필터 규칙 독립

`app/infra/*`:

- 경로/환경변수/상수 제공

`run_gui_backend.py`:

- GUI 외 핵심 공용 비즈니스 로직

`pipeline_post_collect_v1.py`:

- 계약원장/웹 크롤링/당선자 추출 엔진

`export_project_tracker_from_winner_csv.py`:

- 트래커 최종 산출, 원문 재파싱, LLM 보정, 시트 작성

## 17. 재구현 권고 아키텍처

동작 동일성을 최우선으로 할 경우, 아래 순서로 재구축한다.

1. 데이터 계약(CSV/엑셀/큐 이벤트) 먼저 고정
2. `run_post_collect` 동작을 블랙박스 동등 구현
3. tracker export의 `_prepare_one` 규칙을 동일 구현
4. 마지막으로 UI 상태전이/로그를 동일 복제

핵심 원칙:

1. 출력 스키마와 상태 전이를 바꾸지 않는다.
2. 외부 API fallback 순서를 바꾸지 않는다.
3. 연락처/면적/공사비 의심값 가드는 동일하게 유지한다.

## 18. 모듈별 입력/출력 스키마

## 18.1 `run_gui.py` / `app/run_gui.py`

입력:

1. 없음 (CLI 인자 사용 안 함)

출력:

1. Tkinter GUI 프로세스 실행

## 18.2 `app/ui/main_window.py`

입력:

1. 사용자 입력 폼 값
2. 백그라운드 큐 이벤트

출력:

1. 큐 송신 이벤트 `log/error/stopped/done/tracker_done/export_saved/export_error/export_idle`
2. 결과 테이블 표시 (`winner_pipeline_posts_files_v1_1.csv` 최대 500행)

## 18.3 `run_gui_backend.py::fetch_seed_rows`

입력:

1. `service_key: str`
2. `start_date: YYYYMMDD`
3. `end_date: YYYYMMDD`
4. `bid_no_filter: str`
5. `title_filter: str`
6. `demand_org_filter: str`
7. `rows_per_page: int`
8. `max_pages: int`
9. `endpoint_mode: construction|service|goods|all`

출력:

1. `list[dict]` with keys `bid_no,bid_ord,project_name,org_name,announce_date,g2b_verified`
2. 모든 엔드포인트가 429일 때 `AllEndpointsQuotaExceededError`

## 18.4 `pipeline_post_collect_v1.py::run_post_collect`

입력:

1. `internal_nav_csv: Path`
2. `out_csv: Path`
3. `contract_date_hint: str`
4. `lofin_api_key: str`
5. `g2b_service_key: str`
6. `g2b_inqry_bgn_date: YYYYMMDD`
7. `g2b_inqry_end_date: YYYYMMDD`
8. `stop_event`, `progress_cb`

출력:

1. 실제 저장된 CSV `Path` 반환
2. 출력 CSV 필드: `bid_no,bid_ord,rank,project_name_norm,g2b_verified,source_type,internal_search_url,post_url,post_title,winner_name,winner_confidence,winner_pattern,post_score,file_url,file_name,confidence_score,reason_code,review_flag,escalate,contract_name,contract_date,contract_amount,evidence_source,parser_version,run_mode,status,hub_check_note`

## 18.5 `run_gui_backend.py::run_tracker_export_script`

입력:

1. `winner_csv: Path`
2. `seed_csv: Path`
3. `g2b_service_key: str`
4. `demand_org_filter: str`

출력:

1. 후처리 스크립트 실행 결과 엑셀 `Path`
2. 실패 시 `RuntimeError`

## 18.6 `projects/nakchal/scripts/export_project_tracker_from_winner_csv.py::main`

입력:

1. `--winner-csv`
2. `--seed-csv`
3. `--template`
4. `--out`
5. `--notice-json`
6. `--g2b-key`
7. `--demand-org-filter`
8. `--llm-correct`
9. `--anthropic-key`
10. `--llm-model`
11. `--llm-max-rows`

출력:

1. 템플릿 기반 지역별 시트 엑셀 파일
2. stdout에 `written: ...`, `rows: ...` 로그
3. notice raw cache 파일 업데이트

## 19. 주요 알고리즘 로직 설명

## 19.1 계약/당선자 탐색 순서

1. G2B 계약 API 선조회
2. 교육기관이면 EAIS 후 교육청 웹
3. 일반기관이면 LOFIN 후 EAIS 후 HUB
4. 계약 hit 신뢰도가 높으면 게시글 크롤링 스킵
5. 스킵 불가 케이스만 게시글/첨부 크롤링 후 당선자 추출

## 19.2 날짜창 생성 로직

1. `contract_date_hint`가 있으면 해당 기준 우선
2. 없으면 공고일 +30일부터 +210일까지 생성
3. 오늘 이후 날짜는 제외
4. 교육청은 월 단위 descending
5. LOFIN은 일 단위 descending

## 19.3 연락처 추출 로직

1. 공고문 텍스트에서 전화번호 컨텍스트 추출
2. 전화 주변 라인에서 부서 후보 N개 생성
3. 문의/담당 앵커 라인 후보 우선
4. `입찰/계약/지방계약법/조달/회계` 부서는 의심값 처리
5. 후보가 2개 이상이면 LLM 강제 호출
6. LLM이 `contact_selected_idx`로 후보 선택 가능
7. 최종 저장은 `부서/전화` 포맷 유지

## 19.4 면적/공사비 보정 로직

1. 면적은 연면적 강라벨 우선, 대지면적 라벨 감점
2. 건축 프로젝트에서 `<100㎡`는 의심값
3. 공사비는 공사비/총사업비 우선, 설계비/평가비 제외
4. 면적 대비 저가/고가 이상치 필터 적용
5. 필요 시 공고문 재독(`DOC_RECHECK`)으로 2차 보정
6. 필요 시 LLM 보정(`LLM_CORRECTED`) 적용

## 19.5 트래커 행 작성 로직

1. winner/seed/notice raw를 결합해 `_prepare_one` 생성
2. 결과를 다단계 dedupe
3. 지역 기준 그룹핑 후 시트별 작성
4. 템플릿 헤더 매핑 기준으로 값 주입

## 20. 알려진 엣지케이스/운영 이슈

## 20.1 충북교육청 계열 CSV 매핑 갭

현상:

1. 교육청 계약현황 CSV/페이지 구조가 기관별로 다름
2. 헤더명이 달라 계약명/계약일이 누락될 수 있음

대응:

1. `edu_contract_pages_curated_user.csv` 매핑 갱신
2. parser type/기간 파라미터 확인

## 20.2 EDU 라우팅 누락

현상:

1. `org_name`이 교육기관인데도 edu 경로 미진입
2. `EDU_WEB_PAGE_NOT_FOUND` 또는 `EDU_WEB_NO_MATCH` 증가

대응:

1. `_is_education_org_name` 판별 키워드 확장
2. 교육기관 URL 큐레이션 주기적 보정

## 20.3 동일 전화번호 다중 부서 충돌

현상:

1. 같은 번호에 `문의처 부서`와 `입찰/계약 부서`가 같이 등장
2. 잘못된 부서가 선택될 수 있음

대응:

1. 후보 N개 유지 + LLM 선택 인덱스 적용
2. 조달/계약 부서 의심값 필터 유지

## 20.4 공고문 포맷 변형

현상:

1. 전화 패턴 `051)888-5374`, `☎ 061-...` 등 변형
2. 문의 라벨이 줄 분리되어 있을 때 부서 누락

대응:

1. 유연 전화패턴(`PHONE_FLEX_PAT`) 유지
2. 라인+컨텍스트 동시 후보 추출 유지

## 20.5 HWP/HWPX/PDF 추출 품질 저하

현상:

1. 인코딩 깨짐/표 분리 실패로 면적/연락처 오탐 또는 공란

대응:

1. HTML/HWP/HWPX/PDF 포맷별 재시도
2. 저품질 텍스트일 때 LLM/재독 보정

## 20.6 트래커 템플릿 파일 잠금

현상:

1. 사용 중인 엑셀 파일에 저장 실패(`PermissionError`)

대응:

1. 타임스탬프 파일명으로 자동 재저장

## 20.7 LOFIN/EAIS 외부 의존성 변동

현상:

1. 인증/헤더/응답 스키마 변경 시 매칭률 급락

대응:

1. API 호출 로그 기반 즉시 fallback 경로 점검
2. `reason_code` 모니터링으로 이상 탐지

