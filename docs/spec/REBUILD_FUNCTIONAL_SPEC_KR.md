# 현재 구현 기준 재구축 기능명세서

- 문서 역할: 기능명세서
- 정본 여부: `canonical`
- 기준 커밋: `origin/main` = `eaa3b3e28056aa62182eabe284c8db6ce39b7238`
- 작성일: 2026-04-30
- 상위 기준 문서: [DOCUMENT_GOVERNANCE_MATRIX_KR.md](./DOCUMENT_GOVERNANCE_MATRIX_KR.md)
- 기준 마스터 문서: [IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md](./IMPLEMENTED_GAP_AND_REBUILD_SPEC_KR.md)
- 목적: 새 구현팀이 기존 코드 없이도 현재 웹 콘솔의 기능을 95% 이상 유사하게 재구축할 수 있도록 사용자 기능과 업무 흐름을 고정한다.

## 1. 제품 목적

본 제품은 공고/프로젝트 데이터를 수집하고, 프로젝트 단위로 정리한 뒤, 조직 사용자가 영업 기회를 배정/관리/종료할 수 있게 하는 B2B 웹 콘솔이다.

재구축 제품은 아래 기능을 하나의 운영 콘솔로 제공해야 한다.

1. 공고 수집 및 프로젝트 트래커 실행
2. 실행 상태, 로그, 리포트, 산출물 확인
3. 프로젝트 트래커 결과 조회, 수정, 다운로드
4. 관련 공고 조회
5. 영업 대상 프로젝트 claim, 메모, 이관, 해제, 종료
6. 조직 사용자 초대, 계정 관리, 권한 관리
7. 관리자용 감사 로그, 플랫폼 관리자 계정 도구
8. Google Sheets 관리자 조회/동기화
9. report job, tracker download job, home bootstrap 기반 빠른 화면 로딩

## 2. 사용자 역할

역할은 3개로 고정한다.

| 역할 | 설명 | 기능 범위 |
| --- | --- | --- |
| `platform_admin` | 플랫폼 운영자 | 현재 세션 조직 범위의 관리자 기능, 계정 생성/비밀번호 초기화 도구, Google Sheets 관리자, 감사 로그 |
| `org_admin` | 조직 관리자 | 자기 조직 사용자/초대/영업 운영/감사 조회 |
| `org_member` | 일반 사용자 | 사용자 모드, 본인 영업 업무, 프로젝트 조회, claim/release/memo |

현재 구현 기준:

1. `platform_admin`은 모든 조직을 자유롭게 전환하는 전역 UI를 갖지 않는다.
2. `platform_admin` API는 현재 세션의 `organization_id` 범위에서 동작한다.
3. 조직 권한은 `organization_memberships`와 전역 역할을 조합하여 판정한다.

## 3. 인증과 온보딩 기능

### 3.1 로그인

사용자는 이메일과 비밀번호로 로그인한다.

필수 동작:

1. 이메일/비밀번호 입력
2. 로그인 요청
3. 성공 시 authenticated shell 진입
4. 실패 시 오류 메시지 표시
5. 로그아웃 시 unauthenticated shell 복귀

현재 구현 기준:

1. Google login은 MVP 필수가 아니다.
2. Supabase token import 기반 세션 가져오기를 지원한다.
3. auth endpoint 명칭은 `/api/auth/sign-in`, `/api/auth/sign-up`, `/api/auth/sign-out`, `/api/auth/session/import` 계열을 따른다.

### 3.2 초대 기반 가입

공개 자유가입이 아니라 초대 기반 가입을 기본으로 한다.

필수 동작:

1. 관리자가 이메일과 역할을 입력하여 초대한다.
2. 시스템은 초대 링크와 필요 시 초기 암호 또는 fallback 정보를 제공한다.
3. 초대 대상자는 초대 이메일과 같은 이메일로 가입한다.
4. 초대 수락은 중복 membership 없이 idempotent 하게 처리한다.
5. 초대 상태는 `pending`, `accepted`, `expired`, `revoked`를 사용한다.

초대 한도:

1. 조직 plan에 따라 초대/가입 가능 인원을 제한한다.
2. `pending` 초대도 한도 계산에 포함한다.
3. 한도 초과 시 초대 생성 버튼은 실패 메시지를 보여준다.

### 3.3 회원정보

사용자는 본인 프로필을 조회하고 이름 등 허용된 정보를 수정할 수 있어야 한다.

관리자는 조직 사용자 목록에서 사용자의 역할, 소속 상태, 계정 운영 상태를 확인하고 변경할 수 있어야 한다.

## 4. 실행과 리포트 기능

### 4.1 실행 생성

사용자는 프로젝트 트래커 실행을 생성할 수 있어야 한다.

필수 입력:

1. 실행 유형
2. 수집/분석 대상 조건
3. source mode 또는 collect mode
4. 필요한 경우 날짜/키워드/기관/지역 조건

필수 동작:

1. 실행 요청 생성
2. 실행 목록에 즉시 반영
3. queued/running/success/failed/canceled 상태 표시
4. 실행 로그 표시
5. 실행 취소 요청

### 4.2 자동 tracker export

현재 구현 기준:

1. `project_tracker` 실행이 성공하면 `tracker_export` child run이 자동 queue 된다.
2. 같은 parent run 아래 `queued`, `running`, `success` 상태의 child run이 있으면 새 child run을 만들지 않고 재사용한다.
3. 사용자가 수동으로 export를 요청해도 위 재사용 규칙을 따른다.

### 4.3 SSE와 자동 갱신

실행 중 화면은 수동 새로고침 없이 상태가 갱신되어야 한다.

필수 동작:

1. 실행 상태 변경 이벤트 수신
2. 로그 append
3. 최신 리포트와 산출물 갱신
4. 연결 실패 시 polling 또는 수동 새로고침 fallback 제공

### 4.4 리포트 job

사용자는 최신 실행 결과에서 리포트를 생성하거나 다운로드할 수 있어야 한다.

현재 구현 기준:

1. report job은 memory job queue와 file output 기반으로 동작할 수 있다.
2. 장기 운영을 위한 영속 job table은 후속 개선 범위다.
3. UI는 job 진행/완료/실패 상태를 보여줘야 한다.

### 4.5 아티팩트

산출물은 DB metadata와 local filesystem 파일 본문을 조합하여 제공한다.

필수 기능:

1. 산출물 목록 조회
2. 파일 다운로드
3. 텍스트 preview
4. run/report와 artifact 연결 표시

Supabase Storage는 현재 구현 기준의 필수 저장소가 아니다.

## 5. 트래커 기능

### 5.1 트래커 목록

사용자는 프로젝트 트래커 결과를 목록/보드 형태로 조회할 수 있어야 한다.

필수 표시:

1. 프로젝트명
2. 기관/발주처
3. 지역
4. 공고/개찰/마감 관련 날짜
5. 상태
6. 예상 금액 또는 계약 관련 요약
7. 연락처 요약
8. 관련 공고 수
9. 영업 claim 상태

### 5.2 트래커 수정

사용자 또는 관리자는 허용된 editable field를 수정할 수 있어야 한다.

필수 동작:

1. inline edit 또는 상세 drawer에서 수정
2. 원본 값과 override 값을 분리
3. effective value 계산
4. 수정 이벤트 기록
5. 수정 후 목록과 상세 화면 동기화

### 5.3 missing report와 cleanup

관리자는 트래커 데이터 품질을 점검할 수 있어야 한다.

필수 기능:

1. 누락 필드 리포트 조회
2. backfill conflict 확인
3. cleanup preview
4. cleanup apply
5. 적용 결과 요약 표시

### 5.4 contact resolution summary

연락처 추출/선택 결과는 프로젝트 단위로 요약되어야 한다.

필수 표시:

1. 선택된 연락처
2. 선택 근거
3. fallback 여부
4. 원천 정보
5. 사람이 검토해야 하는 경고

## 6. 관련 공고 기능

관련 공고는 단순 링크 목록이 아니라 published snapshot/cache/read path를 가진 별도 기능으로 구현한다.

필수 동작:

1. 프로젝트별 관련 공고 조회
2. 관련 공고 snapshot 조회
3. 캐시된 published 결과 우선 사용
4. 원본 공고 열기
5. 관련도 또는 grouping 근거 표시

## 7. 영업 파이프라인 기능

### 7.1 영업 대상 목록

사용자 모드에는 아래 목록이 있어야 한다.

1. 내가 진행 중인 영업
2. 회사 전체 진행 중인 영업
3. 전체 영업 대상 프로젝트

각 프로젝트는 현재 영업 상태, 담당자, 메모, 종료 여부, 예상/계약 정보, 관련 공고 정보를 보여준다.

### 7.2 claim

사용자는 미배정 프로젝트를 본인 영업 건으로 claim할 수 있어야 한다.

규칙:

1. 이미 다른 사람이 진행 중이면 claim할 수 없다.
2. 관리자 강제 조작은 가능하다.
3. claim 이벤트는 `claim`으로 저장한다.

### 7.3 메모

담당자는 본인 영업 건에 메모를 추가/수정할 수 있어야 한다.

현재 구현 기준:

1. 메모 변경 이벤트는 `note_update`로 저장한다.
2. 관리자 최근 메모 삭제 기능은 현재 구현 호환 기능으로 유지한다.
3. 메모 변경은 감사/이벤트 추적 대상이다.

### 7.4 이관

담당자 또는 관리자는 영업 건을 다른 사용자에게 이관할 수 있다.

현재 구현 기준:

1. 이관은 요청/승인 workflow가 아니라 직접 transfer다.
2. 이벤트명은 `transfer`다.
3. 새 담당자는 같은 조직의 유효 사용자여야 한다.

### 7.5 해제와 종료

영업 건은 해제하거나 종료할 수 있다.

이벤트:

1. `release`
2. `force_release`
3. `close_won`
4. `close_lost`

종료된 건은 진행 중 목록에서 제외하고, 관리자 archive/종료 정리 화면에서 볼 수 있어야 한다.

## 8. Google Sheets 관리자 기능

관리자 모드에는 Google Sheets 관리자 화면이 있어야 한다.

필수 기능:

1. Google Sheets 설정/상태 조회
2. sheet 목록 조회
3. sheet 데이터 snapshot 조회
4. 컬럼 필터
5. 동기화 실행
6. 동기화 결과와 오류 표시
7. 사용자 모드와 분리된 관리자 탭 노출

## 9. home bootstrap과 download job

### 9.1 home bootstrap

초기 화면은 여러 API를 순차 호출하여 느리게 뜨는 방식이 아니라 bootstrap snapshot/cache를 사용해야 한다.

필수 포함:

1. 현재 사용자/조직/권한
2. 최근 실행
3. 최신 리포트
4. 트래커 요약
5. 영업 요약
6. 관리자 알림 또는 감사 요약

### 9.2 tracker download job

대용량 트래커 다운로드는 즉시 응답 파일 생성만 의존하지 않고 job으로 처리할 수 있어야 한다.

필수 동작:

1. 다운로드 job 생성
2. 진행 상태 조회
3. 완료 파일 다운로드
4. 실패 메시지 표시
5. warm/cache 활용

## 10. 완료 기준

재구축 기능 완료 기준:

1. 이메일/비밀번호 로그인부터 사용자 모드 진입까지 동작한다.
2. 관리자 초대, 가입, 소속 생성, 권한 분기가 동작한다.
3. `project_tracker` 실행 생성, 상태 갱신, 로그, 산출물 다운로드가 동작한다.
4. 성공한 tracker 실행 뒤 `tracker_export` child run 재사용/자동 queue가 동작한다.
5. 트래커 목록/수정/관련 공고/missing report/cleanup이 동작한다.
6. 영업 claim/memo/transfer/release/close/archive가 이벤트명 기준으로 동작한다.
7. Google Sheets 관리자 화면에서 sheet 조회/필터/동기화가 동작한다.
8. home bootstrap과 tracker download job이 사용자 체감 성능을 보장한다.

