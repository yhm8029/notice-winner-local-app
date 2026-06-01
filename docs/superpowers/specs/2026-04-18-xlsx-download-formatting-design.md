# XLSX Download Formatting Design

**Date:** 2026-04-18

## Goal

앞으로 사용자에게 내려가는 모든 XLSX 다운로드에서 공통 서식을 적용한다.

- 모든 시트의 사용 중인 셀 글자 크기를 `10`으로 통일한다.
- 모든 시트에서 `2행`을 헤더 행으로 보고 필터를 사용할 수 있게 한다.
- `공고일` 열 값이 `yyyymmdd` 문자열이면 `yyyy-mm-dd` 문자열로 변환한다.

## Scope

이 변경은 현재 사용자 다운로드 경로 두 종류를 포함한다.

1. 템플릿 기반 워크북
- `tracker-entry-summaries` XLSX
- tracker download job XLSX
- sales claims XLSX
- tracker artifact XLSX

2. 코드 생성 워크북
- `tracker missing report` XLSX

스크립트성 XLSX 출력이나 테스트용 파일 생성기는 범위에 포함하지 않는다.

## Design

공통 후처리 함수 하나를 만들어, 워크북이 최종 저장되기 직전에 모든 다운로드 XLSX가 이 함수를 반드시 거치게 한다.

공통 후처리 함수는 다음을 수행한다.

1. 모든 워크시트에 대해 사용 중인 셀 범위를 순회하며 font size를 `10`으로 강제한다.
2. 각 워크시트에서 `2행`부터 마지막 데이터 행까지 `auto_filter.ref`를 설정한다.
3. 각 워크시트의 `2행` 헤더를 읽어, 제목이 `공고일`인 열 아래 값 중 `8자리 숫자`는 `yyyy-mm-dd` 문자열로 바꾼다.

## Placement

- 공통 후처리 함수는 `backend/services/artifact_files.py`에 둔다.
- 템플릿 기반 워크북은 `_build_tracking_workbook(...)` 완료 직전에 후처리를 적용한다.
- `tracker missing report` XLSX는 `backend/api/app.py`의 직접 생성 경로에서 같은 후처리 함수를 호출한다.

## Edge Cases

- 데이터가 없어도 `2행`이 존재하면 필터 범위는 `2행`만 유지한다.
- `공고일` 값이 이미 `yyyy-mm-dd`거나 8자리 숫자가 아니면 그대로 둔다.
- `summary` 같은 시트도 요청 범위상 동일하게 font size와 2행 필터 규칙을 적용한다.

## Verification

- 템플릿 기반 다운로드 테스트에서 다음을 검증한다.
  - 헤더/본문 셀 글자 크기 `10`
  - 각 시트 `auto_filter.ref`가 `2행` 기준으로 설정됨
  - `공고일` 값이 `yyyy-mm-dd`로 변환됨
- missing report XLSX API 테스트에서 다음을 검증한다.
  - 워크북 시트들의 2행 필터 존재
  - 사용 셀 글자 크기 `10`
