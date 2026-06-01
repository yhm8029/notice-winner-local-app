# Tracker Export Site Location Label Design

**Goal**

엑셀 전반에서 중복되어 보이는 `현장위치` 헤더를 명확하게 바꾸고, `현장위치(시군구)`가 비어 있을 때 `발주처 위치`에서 시/군/구를 보정한다.

**Scope**

- `tracker_export` 산출 엑셀
- `project_status_*.xlsx` 다운로드 엑셀
- 템플릿 헤더 해석 로직

**Out of Scope**

- 내부 저장 필드명 변경
- API 응답 스키마 변경
- 상위 추출 파이프라인의 위치 추론 규칙 변경

**Design**

- 내부 필드는 유지한다.
  - `client_location`: 발주처 위치 원문
  - `site_location_1`: 현장위치 시도
  - `site_location_2`: 현장위치 시군구
- 엑셀 헤더 표기는 다음으로 맞춘다.
  - `발주처 위치`
  - `현장위치(시도)`
  - `현장위치(시군구)`
- 기존 템플릿의 `현장위치` 헤더도 계속 지원한다.
- 엑셀 작성 시 `site_location_2`가 비어 있으면 `client_location`에서 시/군/구를 파싱해 채운다.
- 이미 `site_location_2` 값이 있으면 덮어쓰지 않는다.

**Implementation Notes**

- 변경은 `backend/services/artifact_files.py`의 엑셀 렌더링 계층에 한정한다.
- 템플릿 헤더 매핑은 새 이름과 기존 이름을 모두 읽을 수 있게 한다.
- 다운로드용과 산출물용 workbook 생성 경로는 같은 로직을 사용하므로 한 곳 수정으로 같이 반영된다.

**Testing**

- 새 헤더명을 가진 템플릿을 읽을 수 있어야 한다.
- `site_location_2`가 비어 있을 때 `client_location`의 시/군/구가 채워져야 한다.
- `site_location_2`가 이미 있으면 기존 값이 유지되어야 한다.
