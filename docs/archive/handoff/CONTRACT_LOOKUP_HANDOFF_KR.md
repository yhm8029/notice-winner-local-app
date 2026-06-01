# Contract Lookup Handoff

- 문서 역할: handoff 문서
- 정본 여부: `archive`
- 이 문서가 답하는 질문: contract lookup 병목과 당시 변경 맥락은 무엇이었는가
- 상위 기준 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../.../../spec/TECHNICAL_SPEC_KR.md](../.../../spec/TECHNICAL_SPEC_KR.md)

추가 업데이트: 2026-03-18

## 현재 상황

- 최근 병목은 `export(4/5)` 단계의 `attachment_parse`보다 `contract_lookup` 긴 꼬리 쪽이 더 컸다.
- 대표 outlier:
  - `R25BK00555367`
  - `R25BK00562562`
- 실제 로그에서는 `contract_lookup`이 수분 단위로 길어졌고, 이 때문에 `export` 전체가 멈춘 것처럼 보였다.

## 원인 정리

- 현재 `resolve_contract_by_bid_no()` 흐름은 공통적으로 먼저 `G2B direct lookup -> G2B project query sweep`를 탄다.
- 그 뒤 fallback이 갈린다.

### 교육기관일 때

- 판단 기준: `교육청`, `교육지원청`
- 흐름:
  - `G2B`
  - `EAIS`
- `LOFIN`은 타지 않는다.

### 일반 기관일 때

- 기존 흐름:
  - `G2B`
  - `LOFIN`
  - `EAIS`
- 문제:
  - 설계공모 성격의 일반 기관 공고도 `EAIS`에 결과가 있는데, `LOFIN`을 먼저 오래 돌고 나서야 `EAIS`로 내려갔다.
  - 특히 `announce_date + 30일 ~ +210일` 범위의 `LOFIN` date sweep가 길어서 outlier가 생겼다.

## 이번 변경

- 일반 기관 fallback 순서를 다음으로 변경했다.
  - `G2B`
  - `EAIS quick check`
  - `LOFIN`
- 구현 파일:
  - `backend/services/native_contract_lookup.py`
- 테스트 파일:
  - `tests/test_native_contract_lookup.py`

## 확인한 결과

- `R25BK00555367`
  - 변경 전: `contract_lookup`이 약 `596초`
  - 변경 후 단독 확인: 약 `55초`
  - source: `eais_web`
- 즉 긴 꼬리는 크게 줄었지만, 아직 `G2B` query sweep 구간이 앞에 남아 있어서 충분히 빠르다고 보긴 어렵다.

## 아직 하지 않은 것

이번에는 아래는 의도적으로 하지 않았다.

1. `contract_lookup` row-level hard timeout
2. `G2B project query sweep` 범위 축소
3. `LOFIN` 자체 timeout/병렬도 조정

이유:
- 결과 누락 가능성을 아직 계측하지 못했다.
- 우선은 정확도 손실 위험이 낮은 순서 변경만 반영했다.

## 다음 단계 후보

우선순위는 아래 순서가 맞다.

1. 새 서버로 재시작 후 실제 `export` 로그에서 `contract_lookup` 긴 꼬리 감소 확인
2. 일반 기관 중 설계공모 성격에서 `EAIS` hit 비율 확인
3. 그래도 느리면 다음 두 가지를 검토
   - `contract_lookup` row-level hard timeout
   - `G2B query sweep` 범위 축소

## 참고 메모

- 현재 `export`에서 이미 `attachment_parse` 긴 꼬리는 많이 줄어든 상태다.
- 다음 병목은 `contract_lookup` 쪽이다.
- 따라서 다음 튜닝도 `native_contract_lookup.py` 중심으로 보는 게 맞다.

