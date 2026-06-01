# LLM Review Handoff

- 문서 역할: review/handoff 문서
- 정본 여부: `archive`
- 이 문서가 답하는 질문: 당시 LLM 관련 리뷰 요청 범위와 관찰 포인트는 무엇이었는가
- 상위 기준 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../.../../spec/TECHNICAL_SPEC_KR.md](../.../../spec/TECHNICAL_SPEC_KR.md)

추가 업데이트: 2026-03-13

## 목적

퇴근 후 집에서 Claude 코드리뷰를 바로 요청할 수 있도록, 현재 웹 네이티브 이식에서
LLM 관련으로 무엇을 리뷰해야 하는지와 요청 템플릿을 정리한다.

## 현재 상태

- 웹 네이티브 파이프라인에 GUI 형식의 LLM 보정 옵션을 추가했다.
- 현재 웹도 GUI처럼 아래 형식을 받는다.
  - `llm_correct`
  - `anthropic_key`
  - `llm_model`
  - `llm_max_rows`
- 기본 동작은 꺼짐이다.
- LLM은 `연락처`, `연면적`, `공사비` 보정에만 제한적으로 연결했다.
- Anthropic 키와 모델 호출 자체는 확인됐다.
  - 현재 계정에서 호출 가능한 모델 확인: `claude-haiku-4-5-20251001`
- 하지만 LLM을 켜도 일부 실공고에서 GUI와 동일한 결과까지는 아직 못 갔다.

## 현재 핵심 판단

- 문제는 "LLM 연결 실패"가 아니다.
- 문제는 아래 중 하나일 가능성이 높다.
  - GUI의 LLM 입력 문맥 구성 방식이 웹과 다름
  - GUI의 LLM 호출 전/후 필드 판정 규칙이 웹과 다름
  - GUI의 accept/reject 규칙이 웹과 다름
  - 웹이 실제로는 GUI가 쓰는 근거 텍스트를 충분히 못 모으고 있음

## 지금 리뷰해야 하는 함수

### 1차 우선

- repo: `yhm8029/notice-winner-pipeline-project`
- 파일: `projects/nakchal/scripts/export_project_tracker_from_winner_csv.py`
- 함수:
  - `_build_contact_llm_context`
  - `_anthropic_extract_notice_fields`

리뷰 목적:

- 왜 LLM을 켜도 `연락처`, `연면적`, `공사비`가 일부 케이스에서 여전히 안 맞는지 확인
- GUI가 LLM에 어떤 텍스트를 주는지 확인
- GUI가 반환값을 어떤 형태로 기대하는지 확인
- 웹 네이티브로 이식할 때 최소로 반드시 가져와야 하는 규칙 정리

### 2차 우선

- repo: `yhm8029/notice-winner-pipeline-project`
- 파일: `projects/nakchal/scripts/export_project_tracker_from_winner_csv.py`
- 함수:
  - `_llm_evidence_is_noise`
  - `_llm_log_reject`

리뷰 목적:

- GUI가 어떤 경우 LLM 결과를 reject 하는지 확인
- reject 기준이 웹보다 강한지/약한지 확인
- 웹에서 너무 보수적으로 비워두는 문제인지 판단

## 현재 실패 케이스

### R25BK00554120

- GUI:
  - `demand_contact = 시설지원담당/055-960-2791`
- 웹(native + LLM):
  - `demand_contact = 빈값`
- 나머지 핵심 필드는 대부분 일치

### R25BK00570104

- GUI:
  - `gross_area_scale = 3,600㎡`
  - `construction_cost = 150.43억원`
  - `construction_start_date = 계약일 2025-12-16 기준 180일 (완료예정 2026-06-14)`
- 웹(native + LLM):
  - 위 3개가 아직 미일치

## 현재 실공고 비교 결과 요약

### R25BK00554120

- 일치:
  - `winner_name`
  - `contract_amount`
  - `contract_date`
  - `source_type`
  - `reason_code`
  - `project_name`
  - `gross_area_scale`
  - `construction_cost`
  - `demand_org_name`
  - `client_location`
  - `site_location_1`
  - `architect_office`
  - `construction_start_date`
- 미일치:
  - `demand_contact`

### R25BK00570104

- 일치:
  - `winner_name`
  - `contract_amount`
  - `contract_date`
  - `source_type`
  - `reason_code`
  - `project_name`
  - `demand_org_name`
  - `demand_contact`
  - `client_location`
  - `site_location_1`
  - `architect_office`
- 미일치:
  - `gross_area_scale`
  - `construction_cost`
  - `construction_start_date`

## Claude 리뷰 요청 템플릿

### 템플릿 1

```text
프로젝트명 / 리뷰규칙: notice-winner-pipeline-project / P0P1P2 / 출력: 한국어 / 형식: 문제→근거→최소수정안

repo: yhm8029/notice-winner-pipeline-project
파일: projects/nakchal/scripts/export_project_tracker_from_winner_csv.py
함수: _build_contact_llm_context, _anthropic_extract_notice_fields

리뷰항목:
1. 왜 LLM을 켜도 연락처/연면적/공사비가 매칭되지 않는 케이스가 남는지
2. 문제 원인이 입력 문맥 부족인지, 프롬프트 문제인지, 후처리 reject 조건인지
3. GUI 기준에서 LLM 결과를 accept/reject 하는 핵심 규칙이 무엇인지
4. 웹 네이티브 이식 시 최소한 반드시 가져와야 하는 조건이 무엇인지

실패케이스:
- R25BK00554120
  - GUI: demand_contact = 시설지원담당/055-960-2791
  - 웹(native+LLM): demand_contact = 빈값
  - 나머지 핵심 필드는 대부분 일치
- R25BK00570104
  - GUI: gross_area_scale = 3,600㎡
  - GUI: construction_cost = 150.43억원
  - GUI: construction_start_date = 계약일 2025-12-16 기준 180일 (완료예정 2026-06-14)
  - 웹(native+LLM): 위 3개가 아직 미일치

관계 요약:
- 현재 웹은 native pipeline에서 HTML + 첨부(HWP/HWPX/PDF) 텍스트를 합쳐서 area/cost/contact만 선택적으로 LLM 보정함
- Anthropic 호출 자체는 성공 확인됨
- 하지만 GUI와 달리 일부 케이스에서 contact/area/cost가 여전히 비거나 미일치
- 따라서 GUI 원본에서
  - LLM 입력 텍스트를 어떻게 자르는지
  - 어떤 후보군을 주는지
  - evidence를 어떻게 검증하는지
  - 어떤 조건에서 reject 하는지
  를 정확히 확인하려고 함

원하는 답변:
- 문제
- 근거
- 최소수정안
- 가능하면 “웹 이식 시 꼭 옮겨야 할 규칙 3~5개”까지 정리
```

### 템플릿 2

```text
프로젝트명 / 리뷰규칙: notice-winner-pipeline-project / P0P1P2 / 출력: 한국어 / 형식: 문제→근거→최소수정안

repo: yhm8029/notice-winner-pipeline-project
파일: projects/nakchal/scripts/export_project_tracker_from_winner_csv.py
함수: _llm_evidence_is_noise, _llm_log_reject

리뷰항목:
1. contact/area/cost가 실제로 추출돼도 reject 될 수 있는 조건 정리
2. reject 규칙이 과도해서 정상값까지 버리는지 확인
3. 웹 네이티브 이식 시 필수 reject 규칙과 완화 가능한 규칙 분리

실패케이스:
- R25BK00554120: contact 미매칭
- R25BK00570104: area/cost/기간 미매칭

관계 요약:
- 현재 웹은 보수적으로 검증해서 근거 약하면 빈값으로 남김
- GUI도 비슷한 reject 체계가 있는 것으로 보이는데, 실제 reject 기준이 어디까지인지 확인이 필요함
- 목적은 “아무 값이나 채우지 않되, GUI가 채우는 값은 놓치지 않게” 맞추는 것

원하는 답변:
- 문제
- 근거
- 최소수정안
```

## 참고

- 현재 웹 저장소에서 LLM 연결 관련 파일:
  - `backend/services/native_llm_correction.py`
  - `backend/services/native_export_backend.py`
  - `scripts/native_gui_field_compare.py`
- 현재 목표는 "LLM을 더 많이 돌리기"가 아니라 "GUI와 같은 규칙으로 제한적으로 정확하게 돌리기"다.

