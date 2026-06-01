# 현재 구현 기준 재구축 운영/권한/보안 명세서

- 문서 역할: 운영정책, 권한, 보안, 배포 기준 명세서
- 정본 여부: `canonical`
- 기준 커밋: `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238`
- 작성일: 2026-04-30
- 상위 기준 문서: [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./DOCUMENT_GOVERNANCE_MATRIX_KR.md)
- 기준 기능 문서: [REBUILD_FUNCTIONAL_SPEC_KR.md](./REBUILD_FUNCTIONAL_SPEC_KR.md)
- 목적: 현재 구현과 유사한 운영 동작을 재구축하기 위해 계정, 권한, 초대, 감사, 삭제, 영업 운영, 메일, 배포/보안 정책을 고정한다.

## 1. 운영 원칙

1. 모든 업무 데이터는 조직 scope를 가진다.
2. 권한은 전역 역할과 조직 membership 역할의 조합으로 판정한다.
3. 공개 회원가입이 아니라 초대 기반 온보딩을 기본으로 한다.
4. 삭제보다 비활성화/소속 해제를 운영 기본값으로 삼는다.
5. 현재 구현에 존재하는 hard delete API는 호환 기능으로 문서화하되, 일반 운영 절차로 권장하지 않는다.
6. 모든 관리자 조작은 감사 가능한 이벤트를 남긴다.

## 2. 역할과 권한

### 2.1 `platform_admin`

권한:

1. 관리자 모드 접근
2. 현재 조직 범위 사용자/초대/감사 조회
3. 플랫폼 관리자 계정 생성
4. 비밀번호 초기화
5. Google Sheets 관리자 접근
6. 영업 강제 해제/이관/종료 정리

제한:

1. 현재 구현은 조직 전환 UI를 필수로 제공하지 않는다.
2. 전역 모든 조직 일괄 관리는 후속 범위다.

### 2.2 `org_admin`

권한:

1. 자기 조직 `org_member` 초대
2. 사용자 목록 조회
3. 소속 상태 변경
4. 영업 운영 관리
5. 감사 로그 조회
6. 관리자 모드 접근

제한:

1. `platform_admin` 계정 생성 불가
2. 다른 조직 데이터 접근 불가
3. `platform_admin` 전용 도구 접근 불가

### 2.3 `org_member`

권한:

1. 사용자 모드 접근
2. 프로젝트/tracker 조회
3. 본인 sales claim 생성
4. 본인 claim 메모 작성
5. 본인 claim release/transfer 요청 또는 직접 transfer 기능 사용

제한:

1. 관리자 모드 접근 불가
2. 사용자/초대 관리 불가
3. 감사 로그 접근 불가

## 3. 초대 정책

### 3.1 초대 생성

관리자는 이메일, 역할, 필요 시 이름을 입력해 초대를 생성한다.

규칙:

1. 같은 조직에 같은 이메일의 pending 초대가 있으면 중복 생성을 방지한다.
2. 이미 active membership이 있으면 초대하지 않는다.
3. 초대 한도 초과 시 실패한다.
4. 초대 생성 결과는 link fallback을 포함한다.

### 3.2 초대 수락

규칙:

1. 초대 이메일과 가입 이메일이 같아야 한다.
2. 초대 token은 만료될 수 있다.
3. 수락은 idempotent 하다.
4. 이미 수락된 초대 재시도는 기존 membership을 반환하거나 성공 상태로 처리한다.
5. 중복 membership을 만들지 않는다.

### 3.3 초대 메일

운영 기준:

1. 자동 메일 발송을 우선한다.
2. 발송 성공/실패를 UI에 표시한다.
3. 발송 실패해도 초대 링크 fallback을 제공한다.
4. 메일 provider는 교체 가능해야 한다.
5. 운영자는 fallback 링크를 복사해 별도 전달할 수 있다.

## 4. 계정과 소속 상태

### 4.1 계정 상태

계정 상태는 사용자 identity의 운영 상태다.

1. `active`: 로그인 가능
2. `inactive`: 운영상 비활성
3. `disabled`: 차단

### 4.2 소속 상태

소속 상태는 특정 조직 membership의 상태다.

1. `active`: 조직 접근 가능
2. `inactive`: 조직 접근 비활성
3. `invited`: 초대됨
4. `removed`: 소속 제거

### 4.3 전이 규칙

1. `active` 계정이라도 membership이 inactive면 해당 조직 접근은 불가하다.
2. 계정 비활성화는 모든 조직 접근에 영향을 줄 수 있다.
3. 퇴사자 처리는 membership inactive 또는 removed를 기본으로 한다.
4. hard delete는 운영 기본 절차가 아니다.

## 5. 삭제 정책

현재 구현 호환:

1. 사용자 삭제 API가 존재할 수 있다.
2. 연관 데이터 hard delete를 수행하는 동작이 있을 수 있다.

운영 표준:

1. 사용자 퇴사/권한 회수는 비활성화 또는 membership 제거로 처리한다.
2. 영업/감사/다운로드/실행 기록은 보존한다.
3. hard delete는 테스트 데이터, 잘못 생성된 계정, 법적 삭제 요청 등 제한된 상황에서 관리자 승인 후 사용한다.
4. hard delete 실행 전 영향 범위 preview를 제공하는 것이 권장된다.

## 6. 영업 운영 정책

### 6.1 claim

1. 미배정 프로젝트만 일반 사용자가 claim할 수 있다.
2. claim 중복은 transaction으로 방지한다.
3. claim 이벤트는 `claim`으로 기록한다.

### 6.2 메모

1. 담당자는 본인 claim에 메모를 남길 수 있다.
2. 관리자 최근 메모 삭제 기능은 현재 구현 호환 기능으로 둔다.
3. 메모 변경은 `note_update` 이벤트로 기록한다.

### 6.3 이관

현재 구현 기준:

1. 이관은 직접 transfer다.
2. 요청/승인 workflow는 필수가 아니다.
3. 이벤트는 `transfer`로 기록한다.
4. 대상자는 같은 조직의 유효 사용자여야 한다.

### 6.4 해제와 강제 해제

1. 담당자는 본인 claim을 release할 수 있다.
2. 관리자는 force release할 수 있다.
3. 이벤트는 각각 `release`, `force_release`로 기록한다.

### 6.5 종료

종료 유형:

1. `close_won`
2. `close_lost`

종료된 건은 진행 중 목록에서 제외하고 관리자 archive/종료 정리 영역에서 관리한다.

## 7. 감사 로그

필수 감사 대상:

1. 로그인
2. 로그아웃
3. 초대 생성/철회/수락
4. 사용자 역할/상태 변경
5. sales claim action
6. 다운로드
7. Google Sheets sync
8. platform admin 계정 도구 사용
9. hard delete 또는 destructive action

감사 필드:

1. actor user id
2. actor email
3. organization id
4. action type
5. target type
6. target id
7. created at
8. request id
9. metadata JSON

## 8. 보안 기준

### 8.1 비밀 관리

아래 값은 문서나 저장소에 포함하지 않는다.

1. Supabase service key
2. JWT secret
3. Google API credential
4. SMTP password
5. 운영 DB 접속 정보
6. 실제 회사 데이터 export

### 8.2 세션

1. 세션은 secure cookie 또는 동등한 보호 수단으로 관리한다.
2. session import는 서버에서 검증된 token만 허용한다.
3. 만료된 세션은 사용자에게 재로그인을 안내한다.

### 8.3 권한 검사

1. UI 숨김은 보조 장치일 뿐이다.
2. 모든 backend action은 서버에서 role/membership을 다시 검증한다.
3. 조직 scope는 API query와 mutation 모두에서 강제한다.

### 8.4 다운로드 보안

1. 다운로드 요청은 인증이 필요하다.
2. 다운로드 audit log를 남긴다.
3. 임시 파일 또는 job 결과물은 만료 정책을 가진다.

## 9. 배포/운영 기준

필수 환경:

1. production/staging 분리
2. 환경변수 기반 설정
3. DB migration 관리
4. artifact directory 관리
5. log retention
6. background job worker 실행
7. health check endpoint

운영자는 아래를 확인할 수 있어야 한다.

1. API 서버 상태
2. worker 상태
3. DB 연결 상태
4. Google Sheets 연동 상태
5. mail provider 상태
6. artifact storage path 상태

## 10. 클린룸/IP 운영 원칙

재구축 시 새 구현팀에는 아래를 전달하지 않는다.

1. 기존 소스 코드
2. 기존 저장소 전체 clone
3. 실제 회사 영업 데이터
4. 운영 계정 비밀
5. 내부 배포 스크립트 secret

전달 가능한 것:

1. 본 재구축 명세서 세트
2. 비식별 샘플 데이터
3. 화면 동작 설명
4. 공개적으로 재작성 가능한 API 계약
5. 검수 시나리오

## 11. 운영 검수 기준

1. 일반 사용자는 관리자 API를 직접 호출해도 거부된다.
2. 조직 A 사용자는 조직 B 데이터를 볼 수 없다.
3. 초대 수락 재시도는 중복 membership을 만들지 않는다.
4. hard delete 없이도 퇴사자 처리가 가능하다.
5. 모든 sales action은 event와 audit 추적이 가능하다.
6. 다운로드와 Google Sheets sync는 감사 로그에 남는다.
7. secret 없이도 문서 검토가 가능하고, secret은 배포 환경에서만 주입된다.

