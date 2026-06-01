# 내부 SaaS 아키텍처 설계 (Ubuntu 기준)

- 문서 역할: 설계명세 원천 문서
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 현재 GUI 기능을 내부 SaaS로 옮길 때 어떤 구조/경계를 가정했는지
- 이 문서가 답하지 않는 질문: 현재 정본 설계/기술/운영정책의 최종 우선순위
- 상위 기준 문서: [../.../../spec/SYSTEM_DESIGN_KR.md](../.../../spec/SYSTEM_DESIGN_KR.md)
- 충돌 시 우선 문서: [../.../../spec/SYSTEM_DESIGN_KR.md](../.../../spec/SYSTEM_DESIGN_KR.md)

작성일: 2026-03-12  
대상: `notice-winner-pipeline-project`  
목표: 현재 Python GUI 앱을 사내용 내부 웹 SaaS로 옮긴다.

## 1. 범위

포함:
1. 현재 GUI 기능의 웹 이관
2. 실행 요청, 로그 조회, 결과 다운로드
3. 비동기 파이프라인 실행과 상태 관리

제외:
1. 외부 고객 대상 멀티테넌시 과금
2. 공개 가입 결제
3. 기존 추출 알고리즘 변경

## 2. 기술 스택

1. Frontend: `Next.js`
2. Backend API: `FastAPI`
3. Worker: `Celery`
4. Queue/Cache: `Redis`
5. DB/Auth/Storage: `Supabase`
6. 배포 OS: `Ubuntu`
7. Reverse Proxy: `Nginx`

## 3. 핵심 컴포넌트

### 3.1 `web` (Next.js)
- Phase 2 로그인 화면
- 실행 요청 화면
- 실행 이력/상세 화면
- 로그 polling 또는 SSE 구독
- 결과 파일 다운로드

### 3.2 `api` (FastAPI)
- 실행 생성/조회/취소
- 로그 조회
- 결과 파일 메타 조회
- 트래커 재생성 실행 요청
- Supabase DB/Storage 연동

### 3.3 `worker` (Celery)
- 기존 파이프라인 함수 실행
- 상태 변경
- 단계별 로그 기록
- 산출물 업로드

### 3.4 `redis`
- Celery broker/backend
- 단기 캐시

### 3.5 `supabase`
- Auth: Phase 2 로그인 세션
- Postgres: 실행/로그/아티팩트/프리셋
- Storage: CSV/XLSX/로그 파일 저장

## 4. 데이터 흐름

1. 사용자가 웹에서 실행 조건 입력
2. Next.js -> FastAPI `POST /runs`
3. FastAPI가 `pipeline_runs`에 `queued` 생성 후 Celery enqueue
4. Worker가 `running`으로 상태 변경 후 단계 실행
5. 진행 로그를 `pipeline_logs`에 저장
6. `export` 단계에서 부모 run의 필수 산출물(JSON/CSV/XLSX 등) 생성 및 업로드
7. `finalize` 단계에서 부모 run의 `run_artifacts`와 summary 메타를 기록
8. 필수 산출물이 정상 생성되면 부모 run 상태 `success`
9. 사용자가 `POST /api/runs/{run_id}/tracker-export`를 호출하면 새 child run 생성
10. child run이 `tracker_export -> finalize`를 수행하며 tracker XLSX를 생성
11. child run 실패는 부모 run 상태를 변경하지 않음
12. 취소 요청 시 `cancel_requested=true`, Worker는 체크포인트에서 종료

## 5. 상태 모델 원칙

상태값 표준:
- `queued`
- `running`
- `success`
- `failed`
- `cancelled`

진행률 필드:
- `progress_stage`
- `progress_current`
- `progress_total`

취소 필드:
- `cancel_requested`

## 6. 엔터티 표준

표준 테이블명:
1. `users`
2. `pipeline_runs`
3. `pipeline_logs`
4. `run_artifacts`
5. `saved_run_presets`

MVP 선택사항:
1. `projects`

주의:
- `profiles`, `pipeline_outputs`, `progress_pct`, `succeeded` 용어는 사용하지 않는다.

## 7. 로그 전달 방식

표준 정책:
1. `GET /api/runs/{run_id}/logs` 는 JSON polling API
2. `GET /api/runs/{run_id}/events` 는 SSE

MVP:
1. polling 으로 시작 가능
2. SSE 는 동일 데이터의 실시간 전달 채널로 후속 또는 병행 구현 가능

## 8. 인증 방식

표준 정책:
1. Phase 1은 로그인 없이 내부 1인 운영을 전제로 한다
2. Phase 2에서 `Supabase Auth` 기준으로 로그인/세션을 도입한다

정리:
- 별도 `POST /auth/login` 전용 API는 필수 아키텍처로 두지 않는다
- 로그인 화면은 Phase 2에서 프론트의 Supabase Auth 흐름을 사용한다
- 초기 로그인 수단은 `Google 로그인 + 이메일 로그인`을 함께 지원한다
- 가입은 자유가입이 아니라 `초대 기반`을 기본값으로 둔다
- 초대한 이메일과 실제 로그인 이메일은 일치해야 한다
- 동일 이메일의 provider identity는 하나의 사용자에 연결한다
- 회사별 사용자 한도는 `active_user_limit`, `pending_invite_limit` 기준으로 제한한다
- 현재 세션 구현은 signed cookie + refresh 기준이며, `단일 활성 세션`은 후속 hardening으로 검토한다
- 대형 고객사 확장 경로로 `회사 SSO`를 둔다
- 플랫폼 운영자 권한은 조직 사용자 권한과 분리한다
- 초대/가입/재설정 메일은 `Supabase Auth + Custom SMTP` 기준으로 운영한다
- 초기 운영은 `Gmail SMTP`를 임시 채널로 사용한다
- 장기 운영은 `Resend + 회사 도메인 기반 no-reply 발신 주소`로 전환한다
- 상세 정책은 [../operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md](../operations/PHASE2_EMAIL_DELIVERY_AND_SMTP_PLAN_KR.md)를 따른다
- 상세 운영 정책은 [../../PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md](../../PHASE2_AUTH_AND_B2B_OPERATIONS_SPEC_KR.md)를 따른다

## 9. API 경계

필수 앱 API:
1. `POST /api/runs`
2. `GET /api/runs`
3. `GET /api/runs/{run_id}`
4. `POST /api/runs/{run_id}/cancel`
5. `GET /api/runs/{run_id}/logs`
6. `GET /api/runs/{run_id}/events`
7. `GET /api/runs/{run_id}/artifacts`
8. `POST /api/runs/{run_id}/tracker-export`
9. `GET /api/run-presets`
10. `POST /api/run-presets`

## 10. 기존 코드 이관 원칙

이관 대상 핵심 모듈:
1. `run_gui.py`
2. `app/run_gui.py`
3. `pipeline_post_collect_v1.py`
4. `projects/nakchal/scripts/export_project_tracker_from_winner_csv.py`

이관 방식:
1. GUI 위젯/메시지박스 의존만 제거
2. 실행 함수는 worker callable 로 추출
3. `progress_cb` 는 DB 로그 writer 로 연결
4. `stop_event` 는 `cancel_requested` 와 연결
5. 실행 결과 경로는 `run_id` 단위로 분리

## 11. Ubuntu 전환 원칙

PowerShell 보조 로직은 내부 웹 버전에서는 Python HTTP 경로를 우선으로 사용한다.

원칙:
1. 공통 HTTP client 는 `requests.Session` 또는 `httpx`
2. 재시도는 exponential backoff
3. connect/read timeout 분리
4. fallback 순서는 기존 코드 규칙 유지

## 12. 캐시

Redis 캐시 대상:
1. 동일 조건 공고 조회
2. 동일 조건 계약 조회
3. 자주 반복되는 검색 질의 결과

## 13. 체크포인트 확장 정책

MVP:
1. 상태 모델만 고정
2. 재개 기능은 구현하지 않아도 됨

Phase 2:
1. `checkpoint_json`
2. `resume_token`
3. `last_success_stage`

## 14. 보안

1. 내부망 또는 VPN 기반 접근 제한
2. Supabase RLS 적용
3. 조직 단위 데이터 분리
4. 다운로드 URL은 10분(600초) 서명 URL 사용

## 15. 완료 기준

1. 웹에서 현재 GUI와 동일한 입력으로 실행 가능
2. 상태값이 표준 모델에 맞게 일관 동작
3. 로그 조회와 결과 다운로드 가능
4. 트래커 재생성 기능 동작
5. Ubuntu 환경에서 PowerShell 의존 없이 운영 가능

