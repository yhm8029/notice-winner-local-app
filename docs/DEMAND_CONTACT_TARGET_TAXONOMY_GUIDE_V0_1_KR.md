# demand_contact 타깃 정의 · 역할 taxonomy · 라벨링 가이드 v0.1

## 1. 목적

이 문서는 `demand_contact` 필드가 **무엇을 의미하는지**를 먼저 고정하기 위한 문서다.

현재 연락처 추출 문제의 본질은 정규식 품질 부족이 아니라, 아래 성격이 다른 연락처를 하나의 슬롯(`demand_contact`)에 강제로 축약하려는 데 있다.

- 발주처 실무 연락처
- 공모관리기관 연락처
- 접수/제출처 연락처
- 계약/낙찰 단계 연락처
- 일반 안내/기타 연락처

이 문서는 다음 3가지를 정의한다.

1. `demand_contact`의 타깃 정의
2. 연락처 역할 taxonomy
3. 샘플 라벨링 가이드

이 문서는 [CONTACT_SELECTION_RULES_V2_KR.md](./CONTACT_SELECTION_RULES_V2_KR.md)보다 **앞단**의 문서다.
즉, 어떤 후보를 고를지보다 먼저 **무엇을 정답으로 볼지**를 고정한다.

---

## 2. 한 줄 정의

`demand_contact`는 **해당 공고의 현재 단계에서 발주처 측 실무 문의 창구로 사용할 수 있는 연락처**를 의미한다.

좀 더 정확히 말하면:
- 발주기관 본체 또는 발주기관 직속/산하 실무 조직 소속
- 공고/질의/실무 진행 관련 문의 창구로 제시됨
- 문서 내 근거 span이 명확함
- 외부 위탁기관/관리기관/제출처와 구분 가능함

---

## 3. 포함 / 제외 기준

### 3.1 포함 대상

다음 조건을 만족하면 `demand_contact` 후보로 본다.

1. 발주기관 또는 발주기관 산하 실무조직 소속
2. 공고문의 문의처, 담당부서, 전화, 실무 연락처 문맥에서 등장
3. 학교/교육청 문맥에서는 `행정실`도 owner-side practical contact로 허용
4. 특정 부서/담당/실/팀/과/센터/사업소 등 실무 주체로 해석 가능

예:
- `김천시 관광진흥과 권대기 / 054-420-6136`
- `부산정보관광고등학교 행정실 / 051-518-7923`
- `공공건축과 주무관 / 053-xxx-xxxx`
- `도시디자인과 / 055-330-3913`

### 3.2 제외 대상

다음은 `demand_contact`로 직접 채택하지 않는다.

1. 공모관리기관 연락처
2. 설계공모 운영 용역사 연락처
3. 접수처 / 제안서 제출처 연락처
4. 단순 안내 콜센터 / 외부 포털 문의처
5. 계약 단계 전용 연락처를 공모 단계 연락처로 전용한 값
6. 문서 근거 없이 seed/fallback으로만 추정된 값

예:
- `마실와이드 / 02-6010-1022`
- `공모관리기관 마실 / 02-6010-1022`
- `제안서 제출처 / 02-xxxx-xxxx`
- `문의 콜센터 / 1588-xxxx`

### 3.3 애매한 케이스

아래는 문맥과 소속 판단이 필요하다.

- `행정실`
- `공공건축처`
- `체육진흥과`
- `관광진흥과`
- `농촌개발팀`
- 산하기관 / 사업소 / 학교 / 교육지원청 / 특별조직

원칙:
- 발주기관 또는 발주기관 산하 실무조직이면 포함 가능
- 위탁 운영기관 / 외부 관리기관이면 제외
- 불확실하면 자동 확정하지 않고 `review`로 둔다

---

## 4. 역할 taxonomy

연락처 후보는 아래 역할 중 하나로 분류한다.

### 4.1 owner_contact
발주처 본체 또는 발주처 산하 실무조직의 연락처.
최종 `demand_contact`의 1순위 후보.

예:
- `김천시 관광진흥과 / 054-420-6136`
- `행정실 / 051-518-7923`
- `건축주택과 / 053-665-2975`

### 4.2 entrusted_management
공모관리기관, 설계공모 운영 용역사, 평가관리기관 등의 연락처.
문의는 가능하지만 발주처 실무 연락처는 아님.

예:
- `마실와이드 / 02-6010-1022`
- `공모관리기관 마실 / 02-6010-1022`

### 4.3 submission_contact
접수처, 제안서 제출처, 서류 송부처, 방문 제출처 등.
문서 제출용 연락처/창구이며 `demand_contact`와 분리해야 한다.

예:
- `접수처 / 043-201-2582`
- `제안서 제출처 / 02-xxxx-xxxx`

### 4.4 contract_contact
계약 단계 전용 연락처, 낙찰 이후 계약 담당, 계약부서 연락처.
공모 단계 `demand_contact`와는 별도 역할이다.

### 4.5 other_notice_contact
일반 안내, 콜센터, 외부 포털, 문장 파편과 섞인 기타 연락처.
기본적으로 최종 채택 대상이 아니다.

예:
- `등이 변경되었을 경우에는 신속히 우리시 도시디자인과 / 055-330-3913`
- `기타 공모의 진행과 / 052-226-3044`

---

## 5. 단계(phase) 원칙

연락처는 무시간성 단일값이 아니다.
가능하면 아래 phase를 구분해서 해석해야 한다.

- `notice`
- `competition_guideline`
- `submission`
- `contract`
- `result_announcement`

기본 `demand_contact`는 우선 `notice` 단계 또는 공고 수행 실무 문의 문맥의 `owner_contact`를 의미한다.

정리하면:
- `submission_contact`는 따로 보관 가능하지만 `demand_contact` 우선값은 아님
- `contract_contact`는 낙찰 이후 단계의 별도 의미이므로 공모 단계 `demand_contact`로 자동 승격하지 않음

---

## 6. 현재 알고리즘과 안 맞는 지점

현재 구조의 근본 문제는 extractor 자체보다 **resolver 부재**에 가깝다.

### 6.1 단일 슬롯 문제
지금은 서로 다른 역할의 연락처를 모두 `demand_contact` 한 칸에 넣으려 한다.
이 구조에서는 규칙을 더해도 본질적으로 계속 섞인다.

### 6.2 문서 구조 손실
평문 추출 과정에서 부서명과 전화번호를 느슨하게 결합하면, 문장 파편과 다른 문맥의 전화번호가 결합된 “프랑켄슈타인 후보”가 생긴다.

### 6.3 `richness` 편향
부서명/전화번호/설명 문구가 풍부한 후보가 더 좋은 후보처럼 보이지만, 실제로는 외부 공모관리기관/용역사일 가능성이 높다.

### 6.4 시간 축 손실
공고, 지침서, 접수, 계약, 결과공고의 연락처를 모두 단일값으로 접으면, 프로젝트 추적 시스템으로서 단계별 문맥을 잃는다.

### 6.5 seed fallback 오염
추출값과 추정값이 같은 슬롯에 섞이면, 나중에 데이터 품질 진단과 backfill 효과 측정이 어려워진다.

---

## 7. annotation guideline v0.1

### 7.1 라벨링 단위
한 공고에 연락처 후보가 여러 개 있으면, 각 후보마다 아래를 붙인다.

필수:
- `candidate_text`
- `role`
- `phase`
- `owner_side` (`yes` / `no` / `uncertain`)
- `final_pick_for_demand_contact` (`yes` / `no`)
- `reason`
- `evidence_span`

### 7.2 role 라벨 규칙

- 발주기관/산하 실무부서 → `owner_contact`
- 공모관리기관/용역사 → `entrusted_management`
- 접수처/제출처 → `submission_contact`
- 계약/낙찰 이후 담당 → `contract_contact`
- 나머지/문장 파편/외부 포털 → `other_notice_contact`

### 7.3 owner_side 판정 규칙

- 발주기관명 또는 산하기관/학교/교육지원청과 직접 연결되면 `yes`
- 외부 위탁사/관리기관/컨설팅/운영사가 보이면 `no`
- 조직 소속이 모호하면 `uncertain`

### 7.4 final_pick 규칙

`final_pick_for_demand_contact = yes`가 되려면 최소한 다음을 만족해야 한다.

1. `role == owner_contact`
2. `owner_side == yes`
3. phase가 `notice` 또는 공고 실무 문의와 연결됨
4. evidence span이 명확함

그 외는 원칙적으로 `no`.
애매하면 `review` 대상으로 남긴다.

---

## 8. 예시 라벨링

### 예시 1. 섞인 케이스
문장:
- `설계공모 관리용역사 (마실와이드, 02-6010-1022), 김천시 관광진흥과 (권대기 054-420-6136)로 문의`

후보 A:
- `마실와이드 / 02-6010-1022`
- role: `entrusted_management`
- owner_side: `no`
- final_pick: `no`

후보 B:
- `김천시 관광진흥과 권대기 / 054-420-6136`
- role: `owner_contact`
- owner_side: `yes`
- final_pick: `yes`

### 예시 2. 학교 행정실
- `부산정보관광고등학교 행정실 / 051-518-7923`
- role: `owner_contact`
- owner_side: `yes`
- final_pick: `yes`

### 예시 3. 접수처
- `접수처 / 043-201-2582`
- role: `submission_contact`
- owner_side: `uncertain`
- final_pick: `no`

### 예시 4. 문장 파편
- `등이 변경되었을 경우에는 신속히 우리시 도시디자인과 / 055-330-3913`
- role: `other_notice_contact`
- owner_side: `uncertain`
- final_pick: `no`

---

## 9. 평가 지표 분해

최종 `demand_contact` 하나만 보면 어디가 깨졌는지 알 수 없다.
연락처 품질은 최소 아래 4단계로 쪼개서 측정해야 한다.

1. `candidate recall`
- 실제 연락처 후보를 목록에 올렸는가

2. `role classification accuracy`
- 후보의 역할을 제대로 분류했는가

3. `owner-side classification accuracy`
- 발주처 측 연락처인지 구분했는가

4. `final selection precision`
- 최종 `demand_contact`가 맞는가

---

## 10. 권장 전환 순서

### 당장 할 것
1. `demand_contact` 타깃 정의를 이 문서 기준으로 고정
2. 역할 taxonomy 확정
3. 샘플 30~50건 라벨링
4. 현재 추출 결과를 이 taxonomy 기준으로 재관찰
5. 그 다음 resolver 설계

### 그 다음 할 것
1. 후보 생성과 최종 선택을 분리
2. 문서 구조를 유지한 contact observation 레이어 추가
3. `role`, `phase`, `owner_side` 분류기 추가
4. 최종 `demand_contact`는 resolver가 선택

### 나중에 할 것
1. provenance/conflict 저장
2. phase별 연락처 분리 저장
3. low confidence 케이스에만 LLM 보조 사용

---

## 11. LLM 사용 원칙

LLM은 자유 생성기로 두지 않는다.
권장 위치는 아래와 같다.

1. 후보 역할 분류기
- `owner_contact` / `entrusted_management` / `submission_contact` / `contract_contact` / `other`

2. owner-side 판별 보조기
- 발주처 측 실무 연락처인지 분류

3. conflict explanation 보조기
- 왜 후보 A를 선택하고 B를 버렸는지 설명 생성

권장하지 않는 위치:
- 문서 전체를 읽고 `contact` 하나를 자유 생성하게 하는 방식
- 최종값을 LLM이 단독 결정하는 방식

---

## 12. 리뷰 요청 포인트

1. `owner_contact` 정의가 충분히 명확한지
2. `entrusted_management`와 `submission_contact`를 분리하는 게 맞는지
3. 학교/교육청 문맥에서 `행정실`을 owner-side practical contact로 보는 기준이 적절한지
4. `contract_contact`를 별도 role로 유지하는 게 맞는지
5. 현재 한 슬롯(`demand_contact`)을 유지하면서 resolver를 둘지, 장기적으로 필드를 분리할지
6. 라벨링 샘플 수를 30~50으로 시작하는 게 적절한지

---

## 13. 한 줄 결론

지금 문제는 규칙 부족보다 **서로 다른 역할·단계·소속의 연락처를 `demand_contact` 한 슬롯으로 축약하려는 resolver 부재 문제**에 가깝다.

따라서 다음 단계는 규칙 추가가 아니라,
**타깃 정의를 고정하고 observation → role classification → owner-side resolution 구조로 전환하는 것**이다.
