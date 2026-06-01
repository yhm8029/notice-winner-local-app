# 운영/사용자 편의 명세서

- 문서 역할: 운영 편의 기능 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: GUI parity 본체 외에 어떤 운영/사용자 편의 기능을 둘 것인가
- 상위 기준 문서: [02_FUNCTIONAL_SPEC_KR.md](../../spec/FUNCTIONAL_SPEC_KR.md), [05_OPERATION_POLICY_SPEC_KR.md](../../spec/OPERATIONS_POLICY_KR.md)
- 충돌 시 우선 문서: [02_FUNCTIONAL_SPEC_KR.md](../../spec/FUNCTIONAL_SPEC_KR.md)

## 문서 목적
- 이 문서는 GUI parity 자체가 아니라, 웹 콘솔을 더 쓰기 편하게 만들기 위한 운영/사용자 편의 기능을 정리한다.
- 이 문서의 항목은 Phase 1 GUI 동등성 완료 조건과 구분해서 관리한다.

## 문서 경계
이 문서에 포함:
1. 사용자 모드 / 관리자 모드 분리
2. dashboard, recent runs, report UI
3. presets, projects 카드, artifact preview 같은 운영 편의 기능
4. panel modularization 같은 레이아웃 편의 backlog
5. 부모 성공 후 child 자동 생성 같은 콘솔 편의 동작

이 문서에서 제외:
1. GUI parity를 위한 parser/fallback/rescue
2. API/DB 핵심 계약
3. 다중 사용자 인증/권한

## Phase와의 관계
1. Phase 1 기준은 GUI와 기능이 동일한가이다.
2. 이 문서의 항목은 Phase 1 완료 판정의 핵심 근거가 아니다.
3. 이 문서의 항목은 단일 운영자 상태에서도 적용 가능한 콘솔 편의 기능이다.
4. Phase 2의 로그인/권한/협업 기능과도 구분한다.

## 현재 포함 항목

### 1. 사용자 모드 / 관리자 모드
목적:
1. 일반 운영자에게는 필요한 패널만 보이게 한다.
2. 검증, 리포트, 내부 점검 패널은 관리자 모드로 분리한다.

원칙:
1. 모드가 달라도 같은 run과 같은 데이터를 본다.
2. 모드 전환이 run 실행 결과를 바꾸면 안 된다.
3. 모드 전환은 화면 구성 차이여야지 데이터 계약 차이가 되면 안 된다.

### 2. dashboard / recent runs / report UI
목적:
1. 운영 상태를 빠르게 요약한다.
2. parity, artifact diff, 최근 실패 run 같은 검증 보조 정보를 보여준다.

분류:
1. 운영 보조
2. 검증 보조

주의:
1. 이 기능이 있어도 GUI parity 자체가 완성된 것은 아니다.

### 3. presets / projects / artifact preview
목적:
1. 반복 입력을 줄인다.
2. 최근 프로젝트와 산출물을 더 빨리 확인하게 한다.

분류:
1. 사용자 편의
2. 운영 보조

### 4. 부모 성공 후 `tracker_export` 자동 생성
목적:
1. 사용자가 따로 child run 버튼을 누르지 않아도 트래커 엑셀을 바로 확보하게 한다.

원칙:
1. 자동 생성이 되더라도 내부 모델은 `tracker_export` child run으로 유지한다.
2. 수동 재생성 API가 필요한 경우 별도로 남길 수 있다.
3. 자동 생성은 GUI parity 핵심 계약이 아니라 운영 편의 확장으로 본다.

### 5. synthetic / debug 전용 기능
목적:
1. 개발, 테스트, 장애 재현에만 사용한다.

원칙:
1. 일반 운영 모드에서는 노출하지 않는다.
2. 명시적인 debug 플래그가 있을 때만 허용한다.
3. 실데이터 결과와 혼동되면 안 된다.

## backlog

### 1. 콘솔 패널 모듈화
추후 항목:
1. 패널 단위 숨김/표시
2. 패널 순서 재배치
3. 사용자별 레이아웃 저장/복원
4. 필요 시 홈페이지 빌더처럼 패널을 다시 불러오는 편집 모드

### 2. 콘솔 UX 고도화
추후 항목:
1. 더 강한 프로젝트 검색/필터
2. 결과 비교 뷰
3. 운영자용 상태 알림

## 세부 화면 참고
패널별 세부 설명은 아래 문서를 따른다.
- [WEB_CONSOLE_PANEL_GUIDE_KR.txt](./WEB_CONSOLE_PANEL_GUIDE_KR.txt)

