# 프로젝트 그룹핑 릴리스 체크리스트

## 목적
이 문서는 grouping 규칙, related notice score, project identity 로직을 수정할 때
운영 baseline을 깨뜨리지 않도록 확인 절차를 고정하기 위한 체크리스트다.

관련 문서:
1. [PROJECT_GROUPING_QUALITY_KR.md](./PROJECT_GROUPING_QUALITY_KR.md)
2. [SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md](./SAAS_FUNCTIONAL_SPEC_FROM_GUI_KR.md)

고정 기준선:
1. [docs/references/project_grouping_golden_set_v1.csv](./references/project_grouping/project_grouping_golden_set_v1.csv)
2. [docs/references/project_grouping_baseline_v1.summary.json](./references/project_grouping/project_grouping_baseline_v1.summary.json)

## 릴리스 전 확인
1. grouping 관련 변경 파일을 식별한다.
   - 예: `backend/api/app.py`, related notice score helper, project identity helper
2. 이번 변경이 auxiliary / 대행 / 관리 / 평가 용역 제외 규칙에 영향을 주는지 확인한다.
3. golden set 자체는 수정하지 않는다.

## 평가 실행
1. 최신 tracker summary CSV를 준비한다.
2. 아래 명령으로 평가를 실행한다.

```powershell
python scripts/evaluate_project_grouping.py `
  --golden-csv docs/references/project_grouping/project_grouping_golden_set_v1.csv `
  --tracker-csv ._tmp_tracker_entry_summaries.csv `
  --output-stem .tmp-project-grouping/project_grouping_eval_release_check
```

3. 산출물 3종을 확인한다.
   - `*.summary.json`
   - `*.json`
   - `*.csv`

## 승인 기준
1. `pairwise_f1` 하락 금지
2. `overmerged_group_count` 증가 금지
3. `oversplit_group_count` 증가 시 원인 설명 필수
4. 기존 accepted row를 임의로 baseline에서 제외하지 않는다
5. auxiliary / 대행 / 관리 / 평가 용역 제외 판단이 바뀌었다면 사유를 문서화한다

## 반려 기준
1. 서로 다른 사업이 새로 하나의 project로 묶임
2. 기존 stable group이 여러 project로 새로 갈라짐
3. 관련 공고 연결 수는 늘었지만 골든셋 기준 precision이 낮아짐
4. 평가 결과를 남기지 않고 규칙만 수정함

## 릴리스 후 기록
1. 사용한 golden set 버전
2. baseline summary 경로
3. after summary 경로
4. 승인자
5. 대표 개선 케이스
6. 대표 회귀 방지 케이스

## 운영 메모
1. 현재 `v1` 골든셋은 `187 row / 141 group` 기준이다.
2. 다음 확장셋은 singleton 혼동 케이스와 과병합 위험 케이스를 추가해 `300~500 row`를 목표로 한다.
