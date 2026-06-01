# Filter Performance Review Handoff

- 문서 역할: review/handoff 문서
- 정본 여부: `archive`
- 이 문서가 답하는 질문: filter 단계 성능 병목 리뷰 당시 어떤 가설과 관찰이 있었는가
- 상위 기준 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../.../../spec/TECHNICAL_SPEC_KR.md](../.../../spec/TECHNICAL_SPEC_KR.md)

추가 업데이트: 2026-03-18

목적
- `project_tracker`의 `filter` 단계가 아직 전체 체감 시간의 큰 비중을 차지한다.
- 현재 병목이 `병렬화 부족`인지, 아니면 `query fan-out 과다`인지 외부 리뷰를 받기 위한 핸드오프 문서다.
- 이번 리뷰의 목표는 `정확도 손실 최소화`를 전제로 `검색 호출 수 자체를 줄일 수 있는지` 확인하는 것이다.

현재 판단
- `filter`는 이미 row 단위 병렬 처리가 들어가 있다.
- 따라서 1차 의심 병목은 `직렬 실행`이 아니라 `행마다 너무 많은 검색 query를 외부 검색엔진에 보내는 구조`다.
- 특히 `bid_no / project_name / org_name` 조합으로 최대 6개 query를 만들고, 강한 결과를 초반에 찾아도 나머지 query를 끝까지 다 도는 부분이 비효율로 보인다.

관련 코드
- [native_filter_backend.py](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py)

확인한 현재 플로우
1. `run_collect_native`
- 입력 CSV를 읽고 row 단위로 배치 처리한다.
- `_resolve_filter_worker_count`로 워커 수를 정하고, `ThreadPoolExecutor`로 batch 내 row를 병렬 처리한다.
- 즉 row level 병렬성은 이미 있다.

2. `_build_candidate_rows_for_seed_row`
- row에서 `bid_no`, `project_name`, `org_name` 등을 읽는다.
- `bid_ntce_dtl_url` 또는 `bid_ntce_url`가 있으면 `direct_url_fast_path`로 즉시 candidate 1건을 만들고 query 검색을 건너뛴다.
- direct URL이 없으면 `build_queries(...)`로 query 목록을 만들고 `fetch_candidates_from_queries(...)`를 호출한다.

3. `build_queries`
- 현재 최대 6개 query를 만든다.
- 예시 성격:
  - `bid_no + 당선`
  - `bid_no + 결과`
  - `project_name + 당선`
  - `project_name + 결과`
  - `project_name + org_name + 당선`
  - `project_name + org_name + 결과`
- dedupe 후 상위 6개로 자른다.

4. `fetch_candidates_from_queries`
- query를 순서대로 돌면서 `search_google_html(...)`를 호출한다.
- 결과를 official domain 기준으로 거르고 score를 계산한다.
- 강한 candidate가 초반에 나와도 현재는 나머지 query를 끝까지 계속 돈다.

5. `search_google_html`
- query마다 Google HTML 요청 1회
- 실패 시 DuckDuckGo fallback
- 요청 timeout은 8초
- query마다 `sleep(0.2)`가 있다.

현재 추정 병목
1. query fan-out 과다
- row 하나당 최대 6 query
- 각 query는 Google 요청, 실패 시 DuckDuckGo fallback까지 갈 수 있다.

2. 조기 종료 부재
- 이미 충분히 강한 official-domain hit가 나와도 이후 query를 계속 돈다.

3. 같은 의미의 query 반복 가능성
- 월×지역 배치에서 유사한 query가 많이 반복될 수 있는데 현재 run-level query cache가 없다.

현재 코드에서 직접 확인한 함수 위치
- `run_collect_native`
- `_build_candidate_rows_for_seed_row`
- `build_queries`
- `fetch_candidates_from_queries`
- `search_google_html`
- `_search_duckduckgo_html`

지금 생각하는 최소 수정안
1. `fetch_candidates_from_queries`에 조기 종료 추가
- `bid_no` 기반 query에서 official domain + 충분히 높은 score hit가 나오면 남은 query를 중단한다.
- 목표는 정확도를 크게 해치지 않으면서 query 수를 줄이는 것이다.

2. `build_queries`를 2단계 실행 구조로 분리
- 1단계:
  - `bid_no + 당선`
  - `bid_no + 결과`
- 2단계:
  - `project_name + 당선/결과`
  - `project_name + org_name + 당선/결과`
- 1단계에서 강한 hit가 없을 때만 2단계로 내려간다.

3. run-level query cache 추가
- 같은 run 안에서 동일 query를 재요청하지 않도록 메모리 캐시를 둔다.
- 이건 정확도 영향 없이 네트워크 호출 수만 줄이는 방향이다.

지금 하지 않으려는 것
- `filter_row_workers`만 계속 올리는 방식
- `per_query_count`를 공격적으로 줄이는 방식
- official domain / score 규칙 완화
- 검색 정확도를 희생하는 aggressive skip

왜 이 방향이라고 보는지
- 이미 row level 병렬은 있다.
- 실제 비용은 검색엔진 호출 횟수와 timeout/fallback에 더 가깝다.
- 따라서 워커 수만 늘리는 것보다 `한 row가 만드는 외부 호출 수`를 줄이는 것이 더 효과적일 가능성이 높다.

리뷰 요청 템플릿

```text
프로젝트명 / 리뷰규칙: notice-winner-pipeline-web / P0P1P2 / 출력: 한국어 / 형식: 문제→근거→최소수정안

repo: yhm8029/notice-winner-pipeline-web
브랜치: feature/related-notice-search

리뷰 목적:
project_tracker의 filter 단계 병목을 줄이고 싶습니다.
현재는 row 단위 병렬은 이미 들어가 있고, 병목이 query fan-out / 검색 조기 종료 부재 / query cache 부재 쪽이라고 의심하고 있습니다.

파일:
backend/services/native_filter_backend.py

함수:
- run_collect_native
- _build_candidate_rows_for_seed_row
- build_queries
- fetch_candidates_from_queries
- search_google_html
- _search_duckduckgo_html

현재 이해한 플로우:
1. row 단위 병렬 처리
2. direct notice URL이 있으면 fast-path로 즉시 통과
3. direct URL이 없으면 최대 6개 query 생성
4. query마다 Google HTML 검색, 실패 시 DuckDuckGo fallback
5. official domain + score 기반으로 candidate 집계
6. 강한 hit가 있어도 나머지 query를 끝까지 도는 구조

현재 생각하는 개선안:
1. fetch_candidates_from_queries 조기 종료
2. build_queries를 2단계 실행 구조로 변경
3. run-level query cache 추가

질문:
1. 현재 병목 진단이 맞는지
2. 위 3개 중 우선순위가 어떻게 되는지
3. 정확도 손실 최소화 기준에서 가장 안전한 1차 패치가 무엇인지
4. early stop 조건을 어떤 수준으로 잡아야 회귀 위험이 낮은지

원하는 답변:
- 문제
- 근거
- 최소수정안
- 우선순위 높은 개선안 2~3개
```

수정 대상 후보 함수
- [native_filter_backend.py:50](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py:50)
- [native_filter_backend.py:160](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py:160)
- [native_filter_backend.py:372](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py:372)
- [native_filter_backend.py:399](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py:399)
- [native_filter_backend.py:447](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py:447)
- [native_filter_backend.py:491](C:/Users/pc/Desktop/git/notice-winner-pipeline-web/backend/services/native_filter_backend.py:491)

