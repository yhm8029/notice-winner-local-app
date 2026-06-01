# 연면적/공사비 추출 보정 핸드오프

작성일: 2026-04-30

## 목적

`project_status_20260429_001844.xlsx` 기준으로 설계공모 공고의 `연면적`과 `공사비` 누락 원인을 확인하고, 코드 추출만으로 누락을 줄이는 보정을 진행했다. LLM 보정은 사용하지 않았고, 실행 시 `TRACKER_LLM_CORRECT=0` 상태로 검증했다.

## 원본 및 산출물

원본 엑셀은 로컬에 있다.

- `C:\Users\user\Desktop\git\CLI\project_status_20260429_001844.xlsx`

주요 실행 산출물도 로컬 `CLI` 폴더와 repo `output/debug`에 있다.

- `C:\Users\user\Desktop\git\CLI\area_cost_rows601_900_remaining_reviewed_20260430_cp949.csv`
- `C:\Users\user\Desktop\git\CLI\area_cost_rows901_1200_reviewed_20260430_cp949.csv`
- `C:\Users\user\Desktop\git\CLI\area_cost_rows1201_1500_reviewed_20260430_cp949.csv`
- `C:\Users\user\Desktop\git\notice-winner-pipeline-web\output\debug\area_cost_rows601_900_g2b_seed_report.json`
- `C:\Users\user\Desktop\git\notice-winner-pipeline-web\output\debug\area_cost_rows901_1200_g2b_seed_report.json`
- `C:\Users\user\Desktop\git\notice-winner-pipeline-web\output\debug\area_cost_rows1201_1500_g2b_seed_report.json`

G2B 시드 매핑은 서비스키가 있는 EC2에서 실행했고, 결과 CSV/JSON은 다시 로컬 `CLI` 폴더로 가져왔다.

## 코드 변경 요약

### HWP 본문 파싱

`backend/services/attachment_text_extract.py`

- HWP `BodyText/Section*` 스트림을 우선 읽도록 보강했다.
- 압축된 HWP 섹션을 zlib로 해제하고, HWP record 중 text record를 UTF-16LE로 추출한다.
- 기존 `PrvText`만 읽어서 목차 수준에서 끊기던 공고문 본문 표를 더 읽을 수 있게 했다.

### G2B 시드 매핑

`backend/services/native_seed_backend.py`

- 공고번호 필터가 직접 매칭을 놓치는 경우를 줄이기 위해 fallback 수집 경로를 보강했다.
- 숫자형 G2B 공고번호(`20240223277` 등)를 seed에 붙이는 흐름을 개선했다.

### 제외 필터

`backend/services/_native_gui_rules_runtime_support.py`
`backend/services/native_filter_backend.py`
`backend/services/native_rescan_backend.py`

- `제안서 평가용역`, `유지보수`, `운영용역`, `시상식 운영`, `심사시스템`, `심사 중계/송출`, `매뉴얼 제작`, `설계공모 관리`, `홈페이지 이관/재구축`, `리빙랩 운영`, `운영 위탁 용역` 계열을 제외하도록 보강했다.
- seed/direct URL fast path에서도 제외 판정이 먼저 적용된다.
- 이미 `EXCLUDED` 처리된 후보는 rescan 단계로 넘어가지 않는다.

### 연면적 추출

`backend/services/native_gui_rules_area_runtime.py`

- 평 단위 합계를 제곱미터로 환산한다.
- `층별용도 / 면적(㎡)` 표에서 총면적을 추출한다.
- `기존(사업 전) / 증개축(사업 후) / 증감` 표에서 사업 후 소계 연면적을 우선 선택한다.

### 공사비 추출

`backend/services/native_gui_rules_cost_runtime.py`

- `49.8 억 원`처럼 `억`과 `원`이 띄어져 있는 표현도 원 단위로 변환한다.

### 엑셀 export 관련 기존 staged 변경

`backend/services/artifact_files.py`

- tracker download workbook에 auto filter와 border formatting을 적용한다.
- 공고일 표시를 `format_tracker_display_date`로 정규화한다.

## 배치별 리뷰 상태

### 601~900

주요 보정/판정:

- `20240914358`: 설계지침서의 `층별용도 / 면적(㎡)` 표에서 `6,100㎡` 추출 가능하게 보정.
- `20240500251`: 사업 후 소계 `16,278㎡` 선택하도록 보정.
- `20240424698`: `49.8 억 원` 공사비 추출 가능하게 보정.
- `20240408849`: 중복 공고번호 이슈. 부경대 IT 공학관은 공고문에 `8,250㎡`, `25,152,000천원`이 있으나 bid_no 단독 override는 위험해서 수동 override는 하지 않았다.
- 비건축/토목성 4건은 연면적 없음으로 정상 제외.

### 901~1200

정리 완료.

- `20240125589`, `20231148292`, `20230834829`, `20230739620`: 제외키워드 대상.
- `20230829706`: 진입관문 디자인이라 연면적 없음 정상.
- `20230833665`: 교량이라 연면적 없음 정상.
- `20230611543`: 보행녹도라 연면적 없음 정상.
- `20230807107`: Health & Kids Dream Center, 공고번호 보정 후 코드 추출 성공. EAIS `287.75억원` 우선 반영이 맞는 것으로 확인.
- `20230732328`: 드론 테스트베드, 공고번호 보정 후 `3,792㎡`, `12,154,000,000원` 추출 성공.

### 1201~1467

엑셀 원본의 마지막 번호가 1467이라 `1201~1500` 요청은 실제 `1201~1467`로 실행했다.

정리 상태:

- `20230445099`: 광교 중심광장 조성, 광장 조성이라 연면적 없음 정상.
- `20230716581`: 태백 첫생명맞이&아이키움센터, 공고번호 보정 후 `930㎡`, `4,085,000,000원` 추출 성공.
- `20230341904`: 국립중앙의료원, 공고번호 보정 후 `184,810㎡`, `570,101,000,000원` 추출 성공.
- `20230535187`: 중랑천 보행교량, 교량이라 연면적 없음 정상.
- `20230521709`, `20230414950`: 설계공모 관리라 제외 대상.
- `20230416975`: 홈페이지 이관/재구축 용역이라 제외 대상.
- `20230231439`, `20230226204`, `20230127938`, `20230115017`: 설계공모 본건이 아닌 운영/송출/평가성 용역으로 제외 대상.

현재 1201~1467에서 확인 필요로 남긴 건:

- `1294 / 20230525391 / 인천대공원 진입광장 개선사업 설계공모`
  - 광장/조경성 사업으로 보이며 연면적 없음이 정상일 가능성이 높지만, 사용자 최종 판정 전이라 `확인필요`로 남겼다.

## 검증

마지막 관련 테스트:

```powershell
.\.tmp-rebuild-evidence-venv\Scripts\python.exe -m pytest tests\test_native_auxiliary_service_keywords.py tests\test_native_filter_backend.py tests\test_native_rescan_backend.py tests\test_native_tracker_backend.py -q
```

결과:

```text
32 passed in 1.97s
```

더 넓은 관련 테스트는 이전에 아래 묶음으로 통과했다.

```powershell
.\.tmp-rebuild-evidence-venv\Scripts\python.exe -m pytest tests\test_native_area_extraction.py tests\test_native_cost_extraction_units.py tests\test_native_filter_backend.py tests\test_native_rescan_backend.py tests\test_native_auxiliary_service_keywords.py tests\test_native_seed_backend.py tests\test_native_tracker_backend.py
```

결과:

```text
69 passed
```

전체 repo 테스트는 별도 기존 실패가 있어 clean 상태로 보지 않았다. 대표적으로 `test_reextract_supabase_contacts.py`의 `normalize_phone` import 문제와 일부 Supabase/API/temp/contact 계열 실패가 기존 잔여 리스크다.

