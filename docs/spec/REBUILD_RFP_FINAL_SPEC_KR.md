# 재구축 발주용 최종 명세서

- 문서 역할: 외부 개발사/새 구현팀 전달용 최종 발주 명세서
- 정본 여부: `canonical`
- 기준 커밋: `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238`
- 작성일: 2026-04-30
- 상위 기준 문서: [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./DOCUMENT_GOVERNANCE_MATRIX_KR.md)
- 상세 기준 문서:
  - [REBUILD_FUNCTIONAL_SPEC_KR.md](./REBUILD_FUNCTIONAL_SPEC_KR.md)
  - [REBUILD_UI_UX_SPEC_KR.md](./REBUILD_UI_UX_SPEC_KR.md)
  - [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md)
  - [REBUILD_OPERATIONS_SECURITY_SPEC_KR.md](./REBUILD_OPERATIONS_SECURITY_SPEC_KR.md)
- 목적: 기존 소스 코드 없이 현재 제품과 95% 이상 유사한 시스템을 새로 구현하도록 발주 범위, 납품물, 검수 기준, 제외 범위를 명확히 한다.

## 1. 발주 목표

발주 목표는 공고 수집/프로젝트 트래커/영업 파이프라인/조직 운영을 포함한 B2B 웹 콘솔을 신규 구현하는 것이다.

구현 결과물은 아래 조건을 만족해야 한다.

1. 기존 소스 코드를 복제하지 않는다.
2. 본 명세서만으로 기능과 화면을 재구성한다.
3. 현재 구현 기준 주요 사용자 흐름의 95% 이상을 재현한다.
4. 새 회사 또는 새 개발팀이 독립적으로 유지보수할 수 있는 구조로 만든다.
5. 운영 비밀과 실제 회사 데이터 없이 개발/검수할 수 있어야 한다.

## 2. 구축 범위

### 2.1 필수 포함 범위

1. 이메일/비밀번호 로그인, 로그아웃, 세션 유지
2. 초대 기반 가입
3. `platform_admin`, `org_admin`, `org_member` 권한 모델
4. 조직 사용자/초대/소속 관리
5. 프로젝트 트래커 실행 생성/조회/취소
6. 실행 상태, 로그, SSE 또는 fallback 갱신
7. tracker export 자동 queue와 child run 재사용
8. report job
9. artifact preview/download
10. tracker 목록/상세/수정/effective model
11. missing report, cleanup preview/apply
12. contact resolution summary
13. related notice published snapshot/cache/read path
14. sales claim/memo/transfer/release/close/archive
15. 관리자 영업 집계
16. Google Sheets 관리자 조회/필터/동기화
17. home bootstrap
18. tracker download job
19. audit log와 download audit
20. platform admin 계정 생성/비밀번호 초기화 도구

### 2.2 명시적 제외 범위

1. 기존 소스 코드 이전 또는 복제
2. 기존 운영 DB dump 이전
3. 실제 회사 영업 데이터 제공
4. Google login
5. 회사 SSO/SCIM
6. 결제/빌링 phase 3
7. 전역 조직 전환 UI
8. seats 물리 테이블 고도화
9. 영속 report job queue 고도화
10. Supabase Storage 전환

제외 범위는 후속 개선으로 발주할 수 있으나 95% 현재 구현 재현의 필수 조건은 아니다.

## 3. 납품물

필수 납품물:

1. 프론트엔드 애플리케이션 소스 코드
2. 백엔드 API 소스 코드
3. worker/service 소스 코드
4. DB migration
5. 환경변수 목록과 예시 파일
6. 로컬 개발 실행 문서
7. staging/production 배포 문서
8. 관리자 운영 가이드
9. API 명세
10. DB ERD 또는 schema 문서
11. 테스트 코드
12. 검수 시나리오 결과표

납품물은 새 구현팀이 독립적으로 빌드, 테스트, 배포할 수 있어야 한다.

## 4. 구현 단계

### 4.1 1단계: 기반

목표:

1. 프로젝트 구조
2. DB 연결
3. Auth 연결
4. 기본 shell
5. 환경변수

완료 기준:

1. 로그인/로그아웃 가능
2. 세션 유지 가능
3. 조직/사용자 seed로 사용자 모드 진입 가능

### 4.2 2단계: 조직/초대/권한

목표:

1. user profile
2. organization membership
3. invitation
4. role based UI/API guard

완료 기준:

1. 관리자가 사용자를 초대할 수 있다.
2. 초대 수락이 idempotent 하다.
3. 일반 사용자는 관리자 API 접근이 차단된다.

### 4.3 3단계: 실행/run/artifact

목표:

1. run 생성/조회/취소
2. status lifecycle
3. logs/events
4. artifact metadata/file
5. report job

완료 기준:

1. 실행 생성 후 상태가 갱신된다.
2. 성공/실패/취소 상태가 표현된다.
3. artifact preview/download가 가능하다.

### 4.4 4단계: tracker/related notice

목표:

1. tracker entry read/write
2. effective model
3. tracker export child run reuse
4. missing report/cleanup
5. related notice snapshot

완료 기준:

1. tracker 목록과 상세가 표시된다.
2. editable field 수정이 반영된다.
3. related notice가 snapshot/cache 기준으로 열린다.
4. tracker export 자동 queue/reuse가 검증된다.

### 4.5 5단계: sales pipeline

목표:

1. claim
2. memo
3. transfer
4. release/force release
5. close won/lost
6. archive/admin summary

완료 기준:

1. 세 영업 목록이 현재 상태와 일관된다.
2. 모든 action이 지정 event type으로 저장된다.
3. 관리자 강제 조작이 권한 기준으로 제한된다.

### 4.6 6단계: 관리자/Google Sheets/감사

목표:

1. 관리자 탭
2. 감사 로그
3. platform admin tools
4. Google Sheets admin
5. download audit

완료 기준:

1. 관리자 권한 사용자가 관리자 모드로 전환한다.
2. Google Sheets 목록/필터/동기화가 동작한다.
3. 주요 관리자 action이 audit에 남는다.

### 4.7 7단계: 성능/검수/polish

목표:

1. home bootstrap
2. tracker download job
3. empty/error state
4. responsive polish
5. 검수 시나리오 통과

완료 기준:

1. 초기 화면이 bootstrap으로 빠르게 뜬다.
2. 대용량 다운로드가 job 상태로 처리된다.
3. 모든 검수 시나리오가 통과한다.

## 5. 필수 검수 시나리오

### 5.1 인증/초대

1. `org_admin`이 `org_member`를 초대한다.
2. 초대 링크로 가입한다.
3. 같은 링크를 다시 열어도 membership이 중복 생성되지 않는다.
4. `org_member`가 관리자 API를 호출하면 거부된다.

### 5.2 실행/tracker

1. 사용자가 `project_tracker` 실행을 생성한다.
2. 실행이 `queued -> running -> success`로 진행된다.
3. 성공 후 `tracker_export` child run이 생성된다.
4. 같은 parent에서 export를 다시 요청하면 기존 child run을 재사용한다.
5. artifact를 preview/download한다.

### 5.3 tracker 수정/관련 공고

1. tracker 목록에서 프로젝트를 연다.
2. editable field를 수정한다.
3. 원본 값과 override/effective 값이 구분된다.
4. 관련 공고 snapshot이 표시된다.
5. missing report와 cleanup preview가 표시된다.

### 5.4 sales pipeline

1. 미배정 프로젝트를 claim한다.
2. 메모를 추가한다.
3. 다른 사용자에게 transfer한다.
4. release한다.
5. 다시 claim 후 `close_won` 처리한다.
6. 종료된 건이 진행 중 목록에서 빠지고 archive에 보인다.

### 5.5 관리자/Google Sheets

1. `org_admin`이 관리자 모드에 진입한다.
2. 사용자 목록과 초대 목록을 본다.
3. 감사 로그를 조회한다.
4. Google Sheets 목록을 연다.
5. 컬럼 필터를 적용한다.
6. sync를 실행하고 결과를 확인한다.

### 5.6 다운로드/감사

1. tracker download job을 생성한다.
2. job 진행 상태를 확인한다.
3. 완료 파일을 다운로드한다.
4. download audit log에 기록이 남는다.

## 6. 기술 수용 기준

1. API endpoint는 [REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md](./REBUILD_SYSTEM_TECHNICAL_SPEC_KR.md)의 현재 구현 기준을 따른다.
2. sales endpoint는 `/api/sales-claims/projects/{project_id}/...` 형태를 표준으로 한다.
3. auth endpoint는 `/api/auth/sign-in`, `/sign-up`, `/sign-out`, `/session/import` 계열을 표준으로 한다.
4. sales event type은 `claim`, `note_update`, `transfer`, `release`, `force_release`, `close_won`, `close_lost`를 사용한다.
5. artifact는 local file + DB metadata 기준으로 동작한다.
6. report/download job은 memory queue 기반이어도 현재 구현 호환으로 인정한다.
7. 보안상 모든 mutation은 서버에서 권한을 재검증한다.

## 7. UI 수용 기준

1. 사용자 모드와 관리자 모드가 명확히 분리된다.
2. 일반 사용자는 관리자 탭을 볼 수 없다.
3. 실행 상세에서 상태, 로그, artifact, child run을 볼 수 있다.
4. tracker 목록/상세/수정/관련 공고 흐름이 끊기지 않는다.
5. 영업 세 목록이 claim 상태 변화에 따라 일관되게 갱신된다.
6. Google Sheets 관리자 화면은 목록, table, 필터, sync 결과를 제공한다.
7. 모든 loading/error/empty 상태가 화면에 표현된다.

## 8. 보안/IP 조건

발주자는 새 구현팀에 아래를 제공하지 않는다.

1. 기존 소스 코드
2. 기존 저장소 접근 권한
3. 운영 DB dump
4. 운영 secret
5. 실제 고객/영업 데이터

새 구현팀은 아래를 보장해야 한다.

1. 본 명세서를 바탕으로 독립 구현한다.
2. 외부 오픈소스 사용 시 라이선스를 명시한다.
3. 기존 코드 복사 없이 동작/기능 기준으로 재작성한다.
4. 샘플 데이터는 비식별 또는 synthetic 데이터만 사용한다.

## 9. 최종 인수 조건

최종 인수는 아래 조건을 모두 만족해야 한다.

1. 본 문서의 필수 포함 범위가 구현되어 있다.
2. 5장의 필수 검수 시나리오가 통과한다.
3. 일반 사용자, 조직 관리자, 플랫폼 관리자 권한 검수가 통과한다.
4. 데이터 생성/수정/삭제성 action이 감사 가능하다.
5. 로컬 개발 환경에서 신규 개발자가 문서만 보고 실행할 수 있다.
6. staging 환경에서 seed/synthetic 데이터로 전체 흐름을 시연할 수 있다.
7. 기존 코드나 운영 비밀 없이 유지보수 가능한 산출물이 납품된다.

## 10. 후속 개선 후보

아래 항목은 현재 구현 95% 재현 이후 별도 개선으로 다룬다.

1. Google login
2. 회사 SSO/SCIM
3. 전역 조직 전환 UI
4. billing/payment
5. Supabase Storage 또는 object storage 전환
6. 영속 job queue
7. 고급 권한 matrix
8. seats table 고도화
9. 조직도/부서 기능
10. multi-tenant 운영 대시보드

