# Archive Index

- 문서 역할: 아카이브 인덱스
- 정본 여부: `archive`
- 이 문서가 답하는 질문: 어떤 과거 문서가 어떤 이유로 archive로 이동했는가
- 상위 기준 문서: [../00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)
- 충돌 시 우선 문서: [../00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)

## 1. 목적

이 문서는 `handoff / review / experiment` 성격 문서를 정본 경로에서 분리한 뒤, 왜 보관하고 있는지 설명하기 위한 아카이브 인덱스다.

원칙:

1. archive 문서는 보존 대상이다.
2. archive 문서는 현재 구현 기준을 직접 정의하지 않는다.
3. archive 문서의 내용이 정본과 충돌하면 정본이 항상 우선한다.

## 2. 아카이브 분류

### 2.1 handoff

- [CONTRACT_LOOKUP_HANDOFF_KR.md](./handoff/CONTRACT_LOOKUP_HANDOFF_KR.md)

### 2.2 review

- [FILTER_PERFORMANCE_REVIEW_HANDOFF_KR.md](./review/FILTER_PERFORMANCE_REVIEW_HANDOFF_KR.md)
- [LLM_REVIEW_HANDOFF_KR.md](./review/LLM_REVIEW_HANDOFF_KR.md)

### 2.3 experiments

- [RELATED_NOTICE_ALGORITHM_EXPERIMENT_PLAN_KR.md](./experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_PLAN_KR.md)
- [RELATED_NOTICE_ALGORITHM_EXPERIMENT_RESULTS_20260314_KR.md](./experiments/RELATED_NOTICE_ALGORITHM_EXPERIMENT_RESULTS_20260314_KR.md)

### 2.4 notes

- [WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md](./notes/WEB_CONSOLE_ARTIFACT_FOLLOWUP_KR.md)
- [EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md](./notes/EXPORT_ATTACHMENT_AND_PAGE_FETCH_KR.md)
- [PHASE1_OPERATOR_POLICY_SPLIT_KR.md](./notes/PHASE1_OPERATOR_POLICY_SPLIT_KR.md)

## 3. 왜 이동했는가

이 문서들은 모두 의미가 있지만, 아래 이유로 정본/참고 본문 경로에서 분리한다.

1. 현재 구현 기준보다 당시 검토 맥락을 설명하는 비중이 크다.
2. 재구축 시 `현재 기준 문서`로 읽히면 혼선을 만든다.
3. 내용 자체는 여전히 추적/배경 이해에 유용하다.

## 4. 사용 원칙

archive 문서는 아래 용도로만 사용한다.

1. 과거 판단 배경 확인
2. 성능/알고리즘 변경 이력 추적
3. 외부 리뷰 요청 맥락 복원

정본 판단은 아래 문서를 우선한다.

1. [../spec/FUNCTIONAL_SPEC_KR.md](../spec/FUNCTIONAL_SPEC_KR.md)
2. [../spec/SYSTEM_DESIGN_KR.md](../spec/SYSTEM_DESIGN_KR.md)
3. [../spec/TECHNICAL_SPEC_KR.md](../spec/TECHNICAL_SPEC_KR.md)
4. [../spec/OPERATIONS_POLICY_KR.md](../spec/OPERATIONS_POLICY_KR.md)

