# 재구축 검수 체크리스트

- 기준 문서: `docs/spec/REBUILD_RFP_FINAL_SPEC_KR.md`
- 목적: 새 구현팀 산출물이 현재 구현 기준 업무 흐름을 95% 이상 재현하는지 확인한다.

## 1. 인증/초대/권한

- [ ] 미인증 사용자는 로그인 화면만 본다.
- [ ] 이메일/비밀번호 로그인과 로그아웃이 동작한다.
- [ ] `org_admin`이 `org_member`를 초대할 수 있다.
- [ ] 초대 수락은 같은 이메일에서만 성공한다.
- [ ] 초대 수락 재시도는 membership을 중복 생성하지 않는다.
- [ ] 일반 사용자는 관리자 탭과 관리자 API에 접근할 수 없다.
- [ ] `platform_admin`, `org_admin`, `org_member`의 화면과 API 권한이 서버에서 재검증된다.

## 2. 실행/run/artifact

- [ ] `project_tracker` 실행을 생성할 수 있다.
- [ ] run status가 `queued`, `running`, `success`, `failed`, `canceled` 계열로 표현된다.
- [ ] 실행 로그가 조회된다.
- [ ] 성공한 `project_tracker` 뒤 `tracker_export` child run이 자동 queue 또는 재사용된다.
- [ ] 같은 parent의 `queued/running/success` export child가 있으면 새 run을 만들지 않는다.
- [ ] artifact metadata와 local file 다운로드가 연결된다.
- [ ] report job과 tracker download job의 상태가 UI/API에서 일관된다.

## 3. 트래커/관련 공고

- [ ] tracker 목록, 검색, 필터, 정렬이 동작한다.
- [ ] tracker 상세 drawer에서 원본 값, override, effective value가 구분된다.
- [ ] editable field 수정 후 목록과 상세가 같은 값을 표시한다.
- [ ] change event 또는 audit trail이 남는다.
- [ ] missing report가 표시된다.
- [ ] cleanup preview 없이 apply가 수행되지 않는다.
- [ ] related notice는 published snapshot/cache/read path 기준으로 표시된다.

## 4. 영업 파이프라인

- [ ] 미배정 프로젝트를 claim할 수 있다.
- [ ] 이미 active claim이 있는 프로젝트는 일반 사용자가 중복 claim할 수 없다.
- [ ] 메모 변경 이벤트는 `note_update`로 남는다.
- [ ] 이관은 요청/승인이 아니라 직접 `transfer`로 처리된다.
- [ ] 해제/강제 해제 이벤트는 `release`, `force_release`로 구분된다.
- [ ] 종료는 `close_won`, `close_lost`로 구분된다.
- [ ] 종료된 건은 진행 중 목록에서 빠지고 archive/종료 정리에서 보인다.

## 5. 관리자/Google Sheets/감사

- [ ] 관리자 모드 상단 탭이 표시된다.
- [ ] 사용자/초대/소속 상태 관리가 동작한다.
- [ ] platform admin 계정 생성/비밀번호 초기화 도구가 권한 제한된다.
- [ ] Google Sheets 관리자 화면에서 tab 목록, table, 컬럼 필터, sync 상태가 표시된다.
- [ ] 로그인, 초대, 사용자 변경, sales action, 다운로드, Google Sheets sync가 감사 로그에 남는다.

## 6. 클린룸/IP

- [ ] 기존 소스 코드, 운영 DB, 운영 secret을 새 구현팀에 제공하지 않았다.
- [ ] 샘플 데이터는 synthetic 또는 비식별 데이터다.
- [ ] 오픈소스 라이선스 목록을 납품물에 포함했다.
- [ ] 독립 구현 확인서를 제출했다.
