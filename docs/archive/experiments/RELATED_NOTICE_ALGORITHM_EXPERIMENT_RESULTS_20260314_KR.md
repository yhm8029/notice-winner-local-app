# 연관 공고 알고리즘 실험 결과

- 문서 역할: 실험 결과 문서
- 정본 여부: `archive`
- 이 문서가 답하는 질문: 연관 공고 알고리즘 검증 실험에서 어떤 결과가 나왔는가
- 상위 기준 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../.../../spec/TECHNICAL_SPEC_KR.md](../.../../spec/TECHNICAL_SPEC_KR.md)

실험 일시: 2026-03-14  
브랜치: `feature/related-notice-search`

## 목적

`연관 공고 보기` 알고리즘을 바로 바꾸기 전에, 현재 `1건 vs 5건` 문제의 원인을 실험으로 분해한다.

이번 문서는 우선순위 실험 1, 3, 5를 실제로 수행한 결과와, 보조로 실험 2 일부를 함께 기록한다.

## 실험 환경

- repo: `notice-winner-pipeline-web`
- 서비스 키: 형제 GUI repo `.env`의 `DATA_GO_KR_SERVICE_KEY` 로드
- 조회 범위: `2025-03-01 ~ 2025-03-31`
- endpoint mode: `all`
- `rows_per_page=20`
- `max_pages=1`
- `request_timeout_sec=6`

기준 프로젝트:
- `고군농공단지 청년문화센터 건립사업`
- 프로젝트 카드 정보:
  - `project_name = 고군농공단지 청년문화센터 건립사업 건축 설계공모`
  - `project_search_name = 고군농공단지 청년문화센터 건립사업`
  - `issuer_name = 전라남도 진도군`

## 실험 1. phrase match vs token match

실행 query:
- A: `고군농공단지 청년문화센터 건립사업`
- B: `고군농공단지 청년문화센터`
- C: `청년문화센터 건립사업`
- D: `고군농공단지`

### 결과 1-a. 기관명 필터 포함 (`전라남도 진도군`)

| Query | 결과 수 | broad retry |
|---|---:|---|
| A | 0 | True |
| B | 0 | True |
| C | 0 | True |
| D | 0 | True |

관찰:
- 네 query 모두 결과 수가 `0`이었다.
- 그리고 네 query 모두 `title_broad_retry_used=True`였다.

### 결과 1-b. 기관명 필터 제거

| Query | 결과 수 | broad retry |
|---|---:|---|
| A | 56 | True |
| B | 56 | True |
| C | 56 | True |
| D | 56 | True |

상위 공고 예시:
- `재실말천(소하천)(진산면 지방리 114)재해복구사업`
- `엄정천(소하천)(진산면 엄정리 338)재해복구사업`
- `사곡동 상사서로일원 도로재포장공사`
- `구운동 218-1번지 일원 노후 하수관로 교체공사`

관찰:
- 네 query가 모두 동일한 56건으로 수렴했다.
- 결과 품질은 기준 프로젝트와 무관한 공고가 대부분이었다.

### 판정

현재 단계에서는 `phrase 검색 vs token 검색`을 아직 판정할 수 없다.

이유:
- low-level fetch가 네 query 모두에서 broad retry를 타면서 동일한 결과 집합(56건)으로 무너졌다.
- 즉 검색어 shape 차이를 보기 전에 broad retry가 실험을 덮어버리고 있다.

결론:
- `phrase 가설`은 아직 살아 있지만, 현재 실험 결과만으로 확정할 수는 없다.
- 먼저 broad retry 개입을 분리해서 다시 측정해야 한다.

## 실험 3. 기관명 필터 영향

같은 query 셋 A/B/C/D에 대해 기관명 필터 유무만 바꿔 비교했다.

### 결과

| 조건 | A | B | C | D |
|---|---:|---:|---:|---:|
| 기관명 필터 있음 | 0 | 0 | 0 | 0 |
| 기관명 필터 없음 | 56 | 56 | 56 | 56 |

### 판정

기관명 필터는 현재 recall을 `56 -> 0`으로 떨어뜨리는 매우 강한 제약이다.

다만 이 결과 역시 broad retry와 함께 나타났기 때문에, 현재 단계의 안전한 결론은 아래와 같다.

1. 기관명 필터는 분명히 너무 빡빡하다.
2. exact equality 또는 현재 매칭 방식은 연관 공고 retrieval의 hard filter로 쓰기 어렵다.
3. 다음 설계에서는 기관명 필터를 `hard filter`보다 `score 요소`로 낮추는 방향이 유력하다.

## 실험 5. 나라장터 웹 검색결과 vs 현재 endpoint 결과

웹 기준 참조:
- 사용자 제공 스크린샷 기준 `고군농공단지 청년문화센터 건립사업` 검색 시 5건 표시
- 포함된 공고 유형:
  - 용역 3건
  - 공사 2건
- 스크린샷에서 확인된 대표 공고:
  - `고군농공단지 청년문화센터 건립사업 감리용역(건축,기계)`
  - `고군농공단지 청년문화센터 건립사업 폐기물처리 용역`
  - `고군농공단지 청년문화센터 건립사업(전기)`
  - `고군농공단지 청년문화센터 건립사업(건축,기계) ...`
  - `고군농공단지 청년문화센터 건립사업 건축 설계공모`

현재 로컬 endpoint 호출:
- `GET /api/projects/{project_id}/related-notices`
- 대상 project id: `d3170d52-861b-5c3b-b7fe-9d32445c26b0`

### 결과

현재 endpoint 반환 결과는 `2건`이었다.

1. 정답 후보
- `고군농공단지 청년문화센터 건립사업 건축 설계공모`
- `R25BK00742725 / 000`
- `match_score = 144`

2. 오탐 후보
- `목재누리센터 건립사업 기본 및 실시설계 공모(제안)`
- `R25BK00754432 / 000`
- `match_score = 20`
- `match_reason = shared_tokens:건립사업, issuer_match`

### 판정

현재 endpoint는 두 가지 문제가 동시에 있다.

1. recall 부족
- 웹 기준 5건 중 현재 endpoint는 1건의 정답만 안정적으로 잡는다.

2. precision 부족
- `건립사업` 같은 generic token 공유만으로 전혀 다른 프로젝트가 같이 들어온다.

즉 현재 endpoint는 `적게 찾고` 동시에 `엉뚱한 것도 섞는` 상태다.

## 보조 실험 2. generic query 결과 수 cap 감

검색어:
- `건립사업`
- `조성사업`
- `증축공사`
- `청년문화센터`

결과:
- 네 검색어 모두 `56건`
- 네 검색어 모두 `title_broad_retry_used=True`

판정:
- 현재는 generic query cap 임계값을 논의하기 전에, broad retry가 먼저 실험 결과를 덮고 있다.
- 즉 `건립사업`과 `청년문화센터`의 차이도 현재 low-level fetch에서는 관찰되지 않았다.

## 종합 결론

### 확정된 것

1. 현재 `related-notices` endpoint는 `고군농공단지 청년문화센터 건립사업` 기준으로 웹 체감 recall을 따라가지 못한다.
2. 현재 endpoint는 generic token 때문에 false positive도 만든다.
3. 기관명 필터는 현재 구조에서는 지나치게 강하다.
4. low-level fetch의 broad retry가 실험 자체를 흐리고 있다.

### 아직 확정되지 않은 것

1. 나라장터 웹이 실제로 OR/형태소 검색인지
2. OpenAPI가 실제로 phrase 검색인지
3. endpoint 차이가 recall 손실의 본질인지

이 셋은 아직 강한 가설이다.

## 추가 실험. broad retry OFF 재실행

실행 목적:
- broad retry가 실험을 덮고 있으므로, 동일 query를 broad retry 없이 다시 측정한다.

설정:
- `allow_title_broad_retry=False`
- 동일 기간: `2025-03-01 ~ 2025-03-31`
- 동일 query A/B/C/D

### 결과

| 조건 | A | B | C | D |
|---|---:|---:|---:|---:|
| 기관 필터 있음 | 0 | 0 | 0 | 0 |
| 기관 필터 없음 | 0 | 0 | 0 | 0 |

추가 관찰:
- 네 query 모두 `title_broad_retry_used=False`
- 네 query 모두 `matched_endpoints=[]`

### 판정

이 결과는 의미가 크다.

1. 현재 `bidNtceNm` 기반 direct title search 경로는 이 케이스에서 전혀 결과를 못 준다.
2. 따라서 이전 실험에서 보였던 `56건`은 broad retry가 만들어낸 인공적인 결과였다.
3. 지금 단계의 1차 문제는 scoring이 아니라 retrieval 자체다.

즉 현재는:
- broad retry ON -> 너무 넓어짐
- broad retry OFF -> 0건

가 된다.

## 추가 실험. 기관 필터 디버그 샘플

실행 목적:
- broad retry ON 상태에서 기관 필터가 어떤 행을 탈락시키는지 샘플을 본다.

설정:
- query: `고군농공단지 청년문화센터 건립사업`
- 기관 필터: `전라남도 진도군`
- `capture_demand_org_debug=True`

### 결과

- 최종 결과 수: `0`
- broad retry: `True`
- 디버그 샘플 수집: `20건`

샘플 특징:
- 수집된 샘플은 대부분 기준 프로젝트와 무관한 공사/복구사업이었다.
- 예:
  - `충청남도 금산군 진산면`
  - `경상북도 구미시`
  - `서울특별시 강남구`
  - `충청북도 보은군`
  - `경기도 포천시`

모든 샘플에서:
- `matched = N`

### 판정

이 실험은 두 가지를 말해준다.

1. 기관 필터 로그는 정상적으로 들어오고 있다.
2. 하지만 현재는 broad retry가 먼저 완전히 무관한 후보를 대량으로 가져오기 때문에, 기관 필터 디버그만으로는 `관련 공고인데 왜 탈락했는지`를 아직 볼 수 없다.

즉 현재 기관 필터 디버그는 `기관 필터가 무조건 틀렸다`를 보여주는 것이 아니라,
`broad retry가 너무 나쁜 후보를 먼저 가져온다`를 더 강하게 보여준다.

## 다음 단계 제안

다음 구현 전에 아래 순서가 필요하다.

1. direct title search가 왜 0건인지 endpoint/파라미터 기준으로 먼저 파악
2. 기관명 필터를 hard filter가 아니라 score 요소로 실험
3. endpoint별 결과 수 비교 실험 추가
4. 그 다음에야 `multi-query fan-out + merge`를 구현

## 현재 판단

지금 시점에서 바로 확정 가능한 구현 방향은 하나다.

- 현재 구조로는 `single query + current broad retry + current org filter` 조합이 틀렸다.
- 현재 구조로는 `direct title search`와 `broad retry` 사이의 간극이 너무 크다.

즉 다음 구현은 단일 query 보정이 아니라, 먼저 retrieval 실험을 다시 분리한 뒤 진행해야 한다.

