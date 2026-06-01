# 시스템 설계명세서

- 문서 역할: 시스템 설계명세서
- 정본 여부: `canonical`
- 이 문서가 답하는 질문: 어떤 컴포넌트와 책임 분리로 시스템을 구성할 것인가
- 이 문서가 답하지 않는 질문: 화면 카피, API 필드 예시, 운영 우선순위
- 상위 기준 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md), [FUNCTIONAL_SPEC_KR.md](./FUNCTIONAL_SPEC_KR.md)
- 충돌 시 우선 문서: [00_CANONICAL_INDEX_KR.md](../00_CANONICAL_INDEX_KR.md)

작성일: 2026-03-22  
상태: 통합 초안 v1

## 1. 문서 목적

이 문서는 시스템 구조와 컴포넌트 책임을 정리하는 설계 정본이다.

본 문서는 아래 문서를 상위 설계 기준으로 재정리한다.

- [reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md](../reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md)

## 2. 설계 원칙

1. 기능과 구현 계약을 분리한다.
2. 프론트/백엔드/워커/DB/Auth 책임을 명확히 나눈다.
3. 외부 인프라는 사서 쓰고, 도메인 운영 로직은 애플리케이션이 직접 가진다.
4. 조직/권한/영업 파이프라인은 제품 도메인 레이어에서 관리한다.

## 3. 주요 컴포넌트

### 3.1 Frontend

역할:

1. 로그인/세션 진입
2. 실행/트래커/영업 UI 제공
3. 관리자 모드/사용자 모드 분기
4. 결과 다운로드와 상호작용 처리

### 3.2 Backend API

역할:

1. 실행 생성/조회/취소
2. 트래커 조회/수정
3. Auth 세션 브릿지
4. 초대/사용자 관리
5. 영업 claim/이관/종료/완료 처리

### 3.3 Worker

역할:

1. 파이프라인 실행
2. 단계별 로그 기록
3. 산출물 생성
4. tracker export 후처리

### 3.4 Supabase

역할:

1. Auth
2. Postgres 저장소
3. Storage

## 4. 데이터 흐름

### 4.1 파이프라인 흐름

1. 사용자가 실행 요청
2. API가 run 생성
3. Worker가 실행
4. 로그/상태/산출물 저장
5. 필요 시 child `tracker_export` 생성

### 4.2 인증/조직 흐름

1. 사용자가 Supabase Auth 기준으로 로그인
2. 앱이 자체 세션 cookie와 동기화
3. `user_profile`과 `membership`으로 앱 사용자/조직 소속 해석
4. 역할에 따라 화면/기능 노출 분기

보조 흐름:

1. 장기 로그인 유지 시 access token 만료와 refresh token 재발급을 분리해 처리
2. 회원정보 변경 시 현재 비밀번호 재검증을 거친다
3. 초대 링크 진입 시 invitation 검증과 세션 생성/연결을 이어서 처리한다

### 4.3 영업 파이프라인 흐름

1. 사용자가 프로젝트 claim
2. 시스템이 owner 잠금
3. 메모/이관/완료/종료 이벤트 발생
4. 관리자 화면에서 집계

### 4.4 초대/온보딩 흐름

1. 관리자가 초대 생성
2. 시스템이 invitation row와 audit log를 기록
3. 메일 발송 또는 링크 fallback 수행
4. 사용자가 로그인/가입 후 초대 수락
5. membership 생성 또는 기존 profile과 연결

### 4.5 다운로드/산출물 흐름

1. 사용자가 트래커 엑셀 또는 영업 목록 엑셀 다운로드 요청
2. 시스템이 로컬 workbook template 기준으로 데이터 바인딩
3. 다운로드 결과는 화면 표시와 동일한 effective value를 사용
4. 생성된 workbook은 읽기 결과물이며 원본 row를 변경하지 않는다

## 5. 책임 분리 기준

1. Auth는 Supabase가 담당한다.
2. 앱 프로필, 소속, 권한 해석은 애플리케이션이 담당한다.
3. 메일 실제 발송은 `Supabase Auth + Custom SMTP`가 담당한다.
4. 도메인 규칙은 앱이 가진다.

### 5.1 데이터 소유권

각 데이터의 소유 경계는 아래와 같이 고정한다.

1. `auth.users`, access/refresh token, 기본 인증 이벤트
   - Supabase Auth 소유
2. `user_profiles`, `organization_memberships`, `invitations`, `audit_logs`
   - 애플리케이션 도메인 소유
3. `pipeline_runs`, `run_logs`, `run_artifacts`, `tracker_entries`
   - 파이프라인/트래커 도메인 소유
4. `project_sales_claims`, `project_sales_claim_events`
   - 영업 도메인 소유

### 5.2 읽기 모델과 쓰기 모델

1. 쓰기 모델은 원본 row와 이벤트를 기록하는 저장 구조를 우선한다.
2. 읽기 모델은 화면 응답 속도를 위해 summary/derived response를 별도로 구성할 수 있다.
3. UI summary는 화면 최적화 목적이며 원본 계약을 대체하지 않는다.

예시:

1. `내가 진행 중인 영업`은 sales claim 원본에서 파생된 읽기 모델
2. `회사 전체 진행 중인 영업`은 동일 원본을 조직 범위로 펼친 읽기 모델
3. `종료/완료 정리`는 close 상태 기반 읽기 모델

## 6. 도메인 경계

### 6.1 인증 도메인

- 로그인
- 세션
- 프로필
- membership
- 초대

### 6.2 파이프라인 도메인

- run
- log
- artifact
- tracker export

### 6.3 영업 도메인

- claim
- transfer
- close
- audit

### 6.4 운영/관리 도메인

- invitation lifecycle
- membership status change
- audit log inspection
- 종료/완료 정리

### 6.5 메일/온보딩 도메인 경계

- 초대 메일 발송
- 비밀번호 재설정 메일
- SMTP 공급자 교체
- 발신 주소 정책

## 7. 보안/권한 경계

1. `platform_admin`은 전역 역할로 해석하며 조직 역할과 분리한다.
2. 조직별 권한 판단은 `organization_memberships`를 기준으로 한다.
3. 미인증 세션은 보호 API에 접근할 수 없다.
4. 본인 수정과 관리자 수정 가능 범위는 운영정책 문서에서 정의한 범위를 따른다.
5. 자기 자신 초대 금지, 초대 이메일 일치, 비활성화 전 진행 영업 정리 규칙은 백엔드에서 강제한다.

## 8. 확장 원칙

1. B2B 운영 구조를 우선하고, 세부 퍼미션 매트릭스는 후속으로 둔다.
2. seat/SSO/SCIM은 확장 고려만 하고 지금은 설계 여지만 남긴다.
3. 메일 공급자는 바꿀 수 있도록 SMTP 기반 경계를 유지한다.
4. 문서 기준 재구축을 위해 canonical 문서와 reference 문서 경계를 유지한다.

### 8.1 세션 유지 설계 원칙

1. 사용성 중심 역할은 장기 로그인 유지 정책을 우선 적용할 수 있어야 한다.
2. access token 수명과 앱 세션 수명은 분리해서 설계한다.
3. 세션 복구는 refresh 기반으로 처리하되, 권한 해석은 매 요청 또는 세션 재검증 시 다시 수행한다.

## 9. 부속 reference 문서

- [reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md](../reference/source/SAAS_ARCHITECTURE_INTERNAL_UBUNTU.md)
- [reference/operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md](../reference/operations/PHASE_STATUS_AND_UPGRADE_PLAN_KR.md)

## 10. 다음 통합 대상

향후 아래를 더 반영한다.

1. 상세 모듈 경계
2. 프론트 분리 구조
3. Auth/Organization 확장 구조

