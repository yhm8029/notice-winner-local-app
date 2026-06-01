# 연관 공고 알고리즘 검증 실험 계획

- 문서 역할: 실험 계획 문서
- 정본 여부: `archive`
- 이 문서가 답하는 질문: 연관 공고 알고리즘 검증 전에 어떤 가설과 실험 항목을 세웠는가
- 상위 기준 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../.../../spec/TECHNICAL_SPEC_KR.md](../.../../spec/TECHNICAL_SPEC_KR.md)

최종 업데이트: 2026-03-14

## 목적

이 문서는 `연관 공고 보기` 기능의 구현 전에, 현재 알고리즘 가설을 검증하기 위한 실험 항목만 정리한다.

중요:
- 이 문서는 구현 지시서가 아니다.
- 이 문서는 알고리즘 리뷰를 실제 실험 항목으로 쪼갠 검증 계획서다.
- Phase 1 기준은 `GUI와 기능/로직 동일`이므로, 웹 전용 추정 규칙을 늘리기 전에 GUI 기준과 외부 검색 특성을 먼저 검증해야 한다.

## 현재 문제 요약

1. 같은 프로젝트 검색어로 나라장터 웹에서는 여러 건이 보이는데, 현재 웹 `related-notices` API는 1건만 반환하는 케이스가 있다.
2. 반대로 low-level raw search는 broad retry가 걸리면 990건처럼 과도하게 넓어질 수 있다.
3. `project_search_name` 정규화는 아직 GUI와 1:1 동일하다고 보기 어렵다.
4. 현재 `연관 공고 보기`는 카드 클릭 시 live search를 하므로 timeout과 결과 흔들림이 발생한다.

## 이번 단계의 목표

이번 단계에서는 아래 3가지만 확인한다.

1. 현재 API 결과 수가 적은 원인이 `phrase 검색` 때문인지 검증한다.
2. `project_search_name` 정규화가 GUI 기준과 얼마나 맞는지 검증한다.
3. 연관 공고 알고리즘의 다음 구현 방향으로 `multi-query fan-out + merge`가 실제로 필요한지 검증한다.

## 검증 대상 가설

가설 A.
- 현재 API 결과 수가 적은 직접 원인은 단일 phrase 검색에 가깝게 동작하는 검색 방식이다.

가설 B.
- 기관명 필터는 recall 손실의 부차 원인일 수 있으며, exact equality보다는 정규화 후 부분일치가 현실적이다.

가설 C.
- `generic tail collapse`가 발생한 상태에서 broad retry가 걸리면 990건 같은 과확장이 발생한다.

가설 D.
- `multi-query fan-out + merge`가 없으면 나라장터 웹 체감과 비슷한 recall을 얻기 어렵다.

가설 E.
- 지금 `1건 vs 5건` 문제는 단일 요인이 아니라 `phrase 검색`, `기관 필터`, `endpoint 차이`가 섞인 문제일 수 있다.

주의:
- 위 항목은 모두 강한 가설이지 확정 사실이 아니다.
- 특히 `나라장터 웹은 OR 기반`, `API는 phrase 기반`은 지금 단계에서 추정이다.
- 구현 전에 아래 실험으로 먼저 확인한다.

## 대표 샘플 케이스

실험은 최소 아래 케이스를 고정 샘플로 사용한다.

1. `고군농공단지 청년문화센터 건립사업`
2. `목재누리센터 건립사업`
3. `여수시 본청사 별관증축 건립사업`
4. `삼호 건강증진형 보건지소 전환 증축공사`
5. `영암 낭씽이 생물자원 보전시설 조성사업`

## 실험 항목

### 실험 1. phrase match vs token match 검증

목적:
- `1건 vs 5건` 문제의 직접 원인이 단일 phrase 검색인지 확인한다.

기준 검색어 예시:
- `고군농공단지 청년문화센터 건립사업`

실행 query:
- Query A: 전체 phrase 그대로
- Query B: `고군농공단지 청년문화센터`
- Query C: `청년문화센터 건립사업`
- Query D: `고군농공단지`

기록:
- 각 query별 결과 수
- 상위 10건 공고명
- 공고번호 목록
- A와 B/C/D 결과의 교집합

판정:
- B/C/D가 A를 포함하면서 결과 수가 더 많으면 phrase match 가설이 강해진다.

### 실험 2. 결과 수 cap 임계값 탐색

목적:
- 어떤 query가 너무 generic해서 과확장되는지 수치로 확인한다.

비교 검색어:
- `건립사업`
- `조성사업`
- `증축공사`
- `청년문화센터` (비교용 고유명사)

기록:
- 검색어별 결과 수
- 상위 10건의 관련성

판정:
- generic tail과 고유명사의 결과 수 차이가 크면 결과 수 cap 또는 broad query drop 규칙을 도입한다.

### 실험 3. 기관명 필터 영향 측정

목적:
- 결과 수가 적은 원인이 phrase인지, 기관명 필터인지 분리한다.

방법:
- 같은 query를 아래 두 조건으로 비교한다.
  - 기관명 필터 있음
  - 기관명 필터 없음

기록:
- 결과 수 차이
- 공고번호 추가/누락 목록

판정:
- 기관 필터 제거 시 recall이 크게 올라가면 기관명은 hard filter가 아니라 score 요소로 내리는 것이 맞다.

### 실험 4. endpoint 차이 측정

목적:
- 나라장터 웹 검색 5건이 어떤 endpoint 조합으로 복원되는지 확인한다.

방법:
- 같은 검색어를 가능한 endpoint별로 비교한다.
  - 공고 검색 endpoint
  - 낙찰 결과 endpoint
  - 계약 endpoint (가능 시)

기록:
- endpoint별 결과 수
- 공고번호 목록

판정:
- 특정 endpoint 또는 endpoint 조합에서만 recall이 올라가면, 연관 공고는 단일 endpoint가 아니라 다중 소스 조합으로 설계해야 한다.

### 실험 5. 나라장터 웹 검색결과 vs API 결과 1:1 대조

목적:
- recall 손실이 API 자체 한계인지, 현재 알고리즘 문제인지 분리한다.

방법:
- 예시 검색어의 나라장터 웹 검색결과를 수동으로 기록한다.
- 같은 검색어의 Query A~D 결과를 전부 합산하고 공고번호 기준 dedupe 한다.

기록:
- 웹 검색 결과 공고번호 목록
- API fan-out 결과 공고번호 목록
- 교집합 / 웹-only / API-only

판정:
- 웹 5건 중 API fan-out으로 복원 가능한 비율을 구한다.
- 복원률이 낮으면 endpoint/검색 전략 문제다.
- 복원률이 높으면 현재 단일 query 알고리즘 문제다.

### 실험 6. token overlap scoring 튜닝용 케이스 수집

목적:
- fan-out 후 precision을 score로 얼마나 회복할 수 있는지 확인한다.

방법:
- 프로젝트 10~20개를 모은다.
- 각 프로젝트에 대해:
  - 나라장터 웹 기준 정답 공고 목록
  - API fan-out 결과 목록
  - 공고별 token overlap score
  - 기관명 match 여부

기록:
- 정답 공고의 score 분포
- 오답 공고의 score 분포

판정:
- threshold 후보 (`0.3`, `0.5` 등)가 실제로 정답/오답을 얼마나 분리하는지 본다.

## 기록 포맷

각 실험은 아래 형식으로 남긴다.

```text
[케이스]
프로젝트명:
기관명:

[입력]
canonical query:
variant query:
기관 필터:

[결과]
웹 결과 수:
API 결과 수:
fan-out 합산 결과 수:
dedupe 후 결과 수:

[메모]
- 어떤 공고가 추가/누락됐는지
- generic tail collapse 여부
- broad retry 발생 여부
- timeout 여부

[판정]
통과 / 실패 / 추가 확인 필요
```

## 우선순위

지금 당장 먼저 할 실험은 아래 3개다.

1. 실험 1 — phrase match vs token match
2. 실험 3 — 기관명 필터 영향
3. 실험 5 — 나라장터 웹 vs API 1:1 대조

이 3개만 돌려도 `1건 vs 5건` 문제의 직접 원인이 phrase인지, 기관 필터인지, endpoint 차이인지 빠르게 분리할 수 있다.

실험 2, 4, 6은 그 다음 단계다.

## 이번 단계 완료 기준

아래 조건을 만족하면 다음 구현 단계로 넘어간다.

1. `project_search_name` 정규화 기준이 GUI와 비교 가능할 정도로 명확해진다.
2. `1건 vs 5건` 문제의 주원인이 phrase 검색인지, 기관 필터인지, endpoint 차이인지 구분된다.
3. `multi-query fan-out`이 실제로 recall을 높인다는 실험 근거가 생긴다.
4. live search 유지 여부와 precompute 전환 여부를 결정할 근거가 생긴다.

## 다음 구현 단계로 넘길 결정 항목

실험 후 아래 항목을 최종 결정한다.

1. GUI 정규화 함수 1:1 이식 범위
2. query variant 생성 규칙
3. broad retry 폐기 여부 또는 cap 규칙
4. scoring 축과 threshold 초안
5. live search 유지 vs precompute 전환

