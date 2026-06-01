# Job Lifecycle Draft

- 문서 역할: 상태/전이 계약 reference
- 정본 여부: `reference`
- 이 문서가 답하는 질문: 실행 상태와 전이 규칙은 어떻게 정의되는가
- 상위 기준 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)
- 충돌 시 우선 문서: [04_TECHNICAL_SPEC_KR.md](../../spec/TECHNICAL_SPEC_KR.md)

## 목적
- 웹 버전에서 파이프라인 실행 상태를 일관되게 표현하기 위한 상태 모델을 정의한다.
- DB, API, 프론트, 워커가 모두 같은 상태 계약을 사용하도록 한다.
- tracker 품질관리 및 backfill 세부 설계는 [TRACKER_QUALITY_BACKFILL_DESIGN_KR.md](./TRACKER_QUALITY_BACKFILL_DESIGN_KR.md)를 따른다.

## Phase 1 운영 가정
- Phase 1은 내부 1인 운영을 전제로 한다.
- 로그인 없이 사용한다.
- `requested_by`는 internal user 고정 UUID를 사용한다.

## 핵심 원칙
- 실행 단위는 반드시 하나의 최종 상태로 종료된다.
- 로그는 상태와 별개로 append-only로 쌓인다.
- 취소는 요청과 실제 반영 시점을 구분한다.
- 재실행은 기존 run을 재사용하지 않고 새 run을 만든다.

## 상태 목록
- `queued`
- `running`
- `success`
- `failed`
- `cancelled`

## 보조 플래그
- `cancel_requested: boolean`
- `progress_stage: text`
- `progress_current: integer`
- `progress_total: integer`

## 상태 정의

### queued
- 실행 요청이 생성되었고 아직 워커가 잡지 않은 상태
- `started_at`은 비어 있음
- Phase 1 운영 기준으로 `queued`가 5분 이상 지속되면 warning 또는 운영 확인 대상이다

### running
- 워커가 실제 실행을 시작한 상태
- `started_at` 기록
- `progress_stage`와 로그가 계속 갱신됨

### success
- 모든 필수 단계가 정상 종료된 상태
- `finished_at` 기록
- 필수 산출물 목록이 생성되어 있어야 함

### failed
- 실행 도중 예외로 중단된 상태
- `finished_at` 기록
- `error_json`에 오류 타입/메시지/실패 단계 기록

### cancelled
- 사용자의 취소 요청 또는 정책상 중단으로 종료된 상태
- `finished_at` 기록
- 부분 산출물이 남을 수 있음

## 상태 전이표

| 현재 | 이벤트 | 다음 |
|---|---|---|
| `queued` | 워커가 실행 시작 | `running` |
| `queued` | 실행 전 취소 승인 | `cancelled` |
| `running` | 정상 완료 | `success` |
| `running` | 예외 발생 | `failed` |
| `running` | 취소 요청 반영 | `cancelled` |

## 허용하지 않는 전이
- `success -> running`
- `failed -> running`
- `cancelled -> running`
- `success -> failed`

## run_type별 단계 모델

### project_tracker

기본 파이프라인 실행의 단계 순서:

1. `collect`
2. `filter`
3. `rescan`
4. `export`
5. `finalize`

#### 단계 설명
- `collect`: 원천 공고 수집
- `filter`: 프로젝트명 추출/필터링
- `rescan`: 프로젝트 단위 재검색
- `export`: 필수 산출물(JSON/CSV/XLSX 등) 생성
- `finalize`: summary 저장, 아티팩트 등록, 최종 종료 처리

### tracker_export

트래커 정리 저장 전용 child run의 단계 순서:

1. `tracker_export`
2. `finalize`

#### 단계 설명
- `tracker_export`: 기존 `project_tracker` run 산출물을 읽어 트래커 XLSX 생성
- `finalize`: child run 아티팩트 등록, summary 저장, 최종 종료 처리

#### 품질관리 관련 메모
- `tracker_export` 결과는 단순 XLSX 생성에 그치지 않고, `tracker_entries` source 필드와 schedule split source 필드까지 갱신할 수 있다.
- dry-run/apply backfill은 별도 운영 스크립트 흐름이며, 기본 lifecycle 상태 집합(`queued|running|success|failed|cancelled`)은 그대로 따른다.

## tracker_export child run 규칙
- `POST /api/runs/{run_id}/tracker-export`는 기존 run을 다시 열지 않는다.
- 항상 새 child run을 생성한다.
- child run은 `run_type=tracker_export`를 사용한다.
- child run은 `parent_run_id = 원본 project_tracker run id`를 가진다.
- 원본 run의 lifecycle은 `export -> finalize`에서 종료된다.
- tracker export 실패는 child run만 `failed` 처리한다.
- 부모 run 상태는 그대로 유지한다.

## progress 규칙
- `progress_stage`는 현재 단계명
- `progress_total`은 해당 단계 또는 전체 예상 수치
- `progress_current`는 현재까지 처리 수
- 총량을 모르면 `progress_total = 0` 허용

## 취소 모델

### cancel_requested
- 사용자가 취소 버튼을 누르면 `true`
- 워커는 단계 경계 또는 루프 안전 지점에서 확인

### 취소 처리 규칙
- 아직 시작 전이면 `queued -> cancelled`
- 실행 중이면 가능한 가장 빠른 안전 지점에서 중단
- 부분 산출물이 존재하면 삭제하지 않고 남긴다
- 로그에 반드시 취소 원인 기록

## 실패 모델

### error_json 구조
```json
{
  "type": "RuntimeError",
  "message": "Service key is required",
  "stage": "collect"
}
```

### 실패 규칙
- 예외 발생 시 즉시 `failed`
- `finished_at` 필수 기록
- 이미 생성된 산출물은 유지

## 로그 규칙
- 각 상태 전이 시 로그 1건 이상 남긴다
- 각 단계 시작/종료 로그를 남긴다
- API 429, quota, fallback, zero-hit retry는 별도 로그 남긴다
- `tracker_export` 실패는 child run warning/error 로그로 남긴다

## UI 표시 규칙
- `queued`: 대기중
- `running`: 실행중
- `success`: 완료
- `failed`: 실패
- `cancelled`: 취소됨

### 진행률 표시
- `running` 상태에서만 프로그레스바 활성화
- `progress_total > 0`이면 비율 표시
- `progress_total = 0`이면 indeterminate 표시

## API/DB 연결 규칙
- `POST /api/runs` 생성 시 상태는 `queued`
- 워커 시작 시 `running`
- 워커 종료 시 `success/failed/cancelled`
- `POST /api/runs/{run_id}/tracker-export`는 별도 child run 생성
- 프론트는 상태값을 절대 자체 추론하지 않고 API 응답만 사용

## 체크포인트 확장 포인트
- 추후 `resumable` 기능이 필요하면 아래 필드를 추가한다
  - `checkpoint_json`
  - `resume_token`
  - `last_success_stage`

현재 MVP에서는 상태 모델만 고정하고, 재개 로직은 후속 구현으로 둔다.

