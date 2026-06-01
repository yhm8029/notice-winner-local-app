# Export 단계의 Attachment / Page Fetch 설명

- 문서 역할: 아카이브 노트
- 정본 여부: `archive`
- 이 문서가 답하는 질문: export 단계에서 attachment/page fetch가 왜 느린지, 어떤 병목이 있는지
- 이 문서가 답하지 않는 질문: export 단계의 최종 구현 기준, API/DB 계약
- 상위 기준 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../../00_CANONICAL_INDEX_KR.md](../../00_CANONICAL_INDEX_KR.md)

## 배경

`export(native)` 단계는 공고 1건을 최종 winner row로 정리할 때, 공고 상세 페이지 본문과 공고 첨부 파일을 함께 읽어 필요한 값을 추출한다.

이 단계에서 시간이 오래 걸리는 이유는 row마다 다음 작업이 들어가기 때문이다.

1. 공고 페이지 HTML 읽기
2. 첨부 파일 다운로드
3. 첨부 파일 텍스트 파싱
4. 추출 결과 병합

## Page Fetch란

`page fetch`는 공고 상세 페이지 HTML을 가져오는 작업이다.

현재 코드에서는 보통 아래 URL 후보를 사용한다.

- `notice_url`
- `base_url`
- `search_url`

이 페이지들에서 본문 텍스트를 뽑아 다음 필드를 먼저 추출한다.

- `architect_office`
- `demand_contact`
- `gross_area_scale`
- 그 외 비용, 위치, 공사기간 관련 값

페이지 본문만으로 충분한 경우가 많아서, 이 단계는 attachment보다 먼저 시도하는 빠른 경로다.

## Attachment란

`attachment`는 공고에 딸린 파일이다.

예:

- `공고문.hwp`
- `과업지시서.pdf`
- `설계지침.hwpx`

이 파일들은 실제로 다운로드한 뒤 텍스트를 추출해야 한다.
특히 `hwp`, `hwpx`, `pdf`는 네트워크 I/O뿐 아니라 파일 파싱 비용도 크다.

즉 attachment 경로는 보통 export에서 가장 무거운 부분이다.

## 왜 줄였는가

기존 구조는 다음 문제가 있었다.

1. 페이지를 여러 개 읽음
2. 첨부를 최대 8개까지 시도함
3. 페이지 본문에서 이미 충분한 정보가 있어도 attachment를 계속 읽음

이 구조는 recall에는 유리할 수 있지만 운영 성능에는 불리하다.

## 이번 최적화 내용

### 1. timing log 추가

각 row 처리 시 아래 시간을 로그로 남긴다.

- `contract_lookup`
- `page_fetch`
- `attachment_download`
- `attachment_parse`

예:

```text
timing_ms(contract_lookup=120,page_fetch=340,attachment_download=1800,attachment_parse=950)
```

이 로그로 다음 최적화가 어느 단계에 효과가 있었는지 수치로 판단할 수 있다.

### 2. page fetch 1개 우선

이제는 페이지를 처음부터 3개 다 읽지 않는다.

우선순위:

1. `notice_url`
2. `base_url`
3. `search_url`

먼저 1개만 읽고, 페이지 본문에서 핵심 필드가 부족할 때만 나머지 URL을 확장한다.

### 3. early stop

페이지 본문에서 아래 3개가 이미 채워지면 attachment를 아예 읽지 않는다.

- `architect_office`
- `demand_contact`
- `gross_area_scale`

즉 페이지에서 충분히 추출된 row는 attachment 다운로드/파싱 비용을 통째로 생략한다.

### 4. attachment 상한 축소

기존:

- 최대 8개

현재:

- 최대 3개

우선순위는 파일명 점수 기준으로 정렬한다.
즉 공고문/지침서/과업지시서 같은 첨부를 먼저 시도하고, 낮은 우선순위 첨부는 기본 경로에서 제외한다.

## 기대 효과

### 장점

- export 단계 체감 속도 개선
- 첨부 다운로드 수 감소
- HWP/PDF 파싱 비용 감소
- row당 네트워크 호출 수 감소
- timing log 기반 추가 최적화 가능

### trade-off

- 핵심 정보가 4번째 이후 첨부에만 있는 드문 케이스는 놓칠 수 있다
- 첫 페이지에 정보가 없고 두 번째/세 번째 페이지에만 있는 케이스는 추가 fetch가 필요하다

그래서 현재 최적화는 공격적으로 다 자른 것이 아니라, 다음 원칙으로 조정했다.

- 페이지 1개 먼저
- 부족하면 추가 페이지
- 핵심 3개가 이미 있으면 attachment skip
- attachment는 상위 3개까지만

## 운영 관점 정리

한 줄로 요약하면:

- `page fetch`는 공고 상세 웹페이지를 읽는 빠른 경로
- `attachment`는 첨부 파일을 다운로드해서 파싱하는 무거운 경로
- 운영 성능을 위해서는 페이지에서 충분히 얻고, attachment는 정말 필요한 경우에만 읽는 쪽이 맞다

