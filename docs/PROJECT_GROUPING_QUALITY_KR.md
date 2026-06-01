# 프로젝트 그룹핑 품질 측정 체계

## 목적
- 이 문서는 `project_id` / `project_search_name` 기반 그룹핑 품질을 운영 지표로 관리하기 위한 측정 체계를 정의한다.
- 목표는 “연관 공고가 잘 열리는가”를 넘어서, 같은 사업이 같은 프로젝트로 안정적으로 묶이는지를 계량화하는 것이다.

## 왜 필요한가
프로젝트 트래커 제품에서 가장 큰 오염 포인트는 개별 필드 누락보다 `잘못된 프로젝트 병합` 또는 `잘못된 프로젝트 분리`다.

실패 유형:
1. 과병합: 서로 다른 사업이 하나의 project로 묶임
2. 과분리: 같은 사업이 여러 project로 쪼개짐

따라서 그룹핑 품질은 필드 fill rate와 별도로 추적해야 한다.

## 측정 대상
현행 grouping 로직은 아래 생산 경로를 사용한다.
1. `backend/api/app.py::_build_project_aggregates`
2. `backend/api/app.py::_derive_tracker_entry_project_identity`
3. `backend/api/app.py::_project_match_key`
4. `backend/api/app.py::_annotate_tracker_entries_with_project_refs`

즉 측정은 “현재 production 로직이 golden set을 얼마나 잘 복원하는가”를 본다.

## 골든셋 포맷
기본 포맷은 CSV다.

필수 컬럼:
1. `expected_group_id`

식별 컬럼 중 하나 이상:
1. `item_key`
2. `entry_key`
3. `bid_no` + `bid_ord`

선택 컬럼:
1. `project_name`
2. `note`

예시:

```csv
expected_group_id,bid_no,bid_ord,project_name,note
group-a,R25BK00000001,000,여수시 본청사 별관증축 건립사업,정답군 1
group-a,R25BK00000002,000,여수시 본청사 별관증축 건립사업 기본 및 실시설계,정답군 1
group-b,R25BK00000003,000,고군농공단지 청년문화센터 건립사업,정답군 2
```

## 현재 고정 운영 골든셋
현재 운영 기준선으로 아래 파일을 고정한다.

1. [docs/references/project_grouping_golden_set_v1.csv](./references/project_grouping/project_grouping_golden_set_v1.csv)
2. [docs/references/project_grouping_golden_set_v1.summary.json](./references/project_grouping/project_grouping_golden_set_v1.summary.json)
3. [docs/references/project_grouping_baseline_v1.summary.json](./references/project_grouping/project_grouping_baseline_v1.summary.json)

현행 고정 기준선 요약:
1. accepted row: `187`
2. accepted group: `141`
3. excluded row: `15`
4. needs_review: `0`
5. baseline pairwise precision / recall / F1: `1.0 / 1.0 / 1.0`

의미:
1. 이 골든셋은 “현재 로직을 고정한 첫 내부 기준선”이다.
2. 이후 grouping 규칙을 변경할 때는 반드시 이 골든셋으로 재평가한다.
3. 새 규칙이 이 기준선을 깨면 채택하지 않는다.

## 평가 지표

### 1. Pairwise Precision
- 같은 predicted group에 들어간 notice pair 중 실제로도 같은 expected group인 비율
- 과병합을 잘 잡는 지표

### 2. Pairwise Recall
- 같은 expected group에 속한 notice pair 중 predicted group에서도 같이 묶인 비율
- 과분리를 잘 잡는 지표

### 3. Pairwise F1
- precision/recall의 균형 지표

### 4. Overmerged Group Count
- 하나의 predicted group 안에 복수 expected group이 섞인 개수

### 5. Oversplit Group Count
- 하나의 expected group이 복수 predicted group으로 갈라진 개수

## 운영 산출물
평가 스크립트는 아래 산출물을 남긴다.
1. `*.summary.json`
2. `*.json`
3. `*.csv`

요약에는 최소 아래가 있어야 한다.
1. `item_count`
2. `expected_group_count`
3. `predicted_group_count`
4. `pairwise_precision`
5. `pairwise_recall`
6. `pairwise_f1`
7. `overmerged_group_count`
8. `oversplit_group_count`

## 사용 스크립트
- [scripts/evaluate_project_grouping.py](../scripts/evaluate_project_grouping.py)

기본 명령:

```powershell
python scripts/evaluate_project_grouping.py `
  --golden-csv docs/references/project_grouping/project_grouping_golden_set_v1.csv `
  --tracker-csv ._tmp_tracker_entry_summaries.csv `
  --output-stem .tmp-project-grouping/project_grouping_eval_sample
```

## 운영 절차
운영 시에는 아래 순서를 고정한다.

1. 기준선 유지
   - `docs/references/project_grouping/project_grouping_golden_set_v1.csv`는 운영 baseline으로 고정한다.
2. 규칙 변경 전
   - 현재 baseline summary를 보존한다.
3. 규칙 변경 후
   - 같은 golden set으로 `scripts/evaluate_project_grouping.py`를 다시 실행한다.
4. 비교
   - `pairwise_f1`, `overmerged_group_count`, `oversplit_group_count`를 baseline과 비교한다.
5. 승인 또는 반려
   - 채택 기준을 만족하면 승인
   - 아니면 규칙 반려 또는 수정 후 재실행

자세한 체크리스트는 [PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md](./PROJECT_GROUPING_RELEASE_CHECKLIST_KR.md)를 따른다.

## 채택 기준
신규 grouping 규칙은 아래 조건을 만족해야 채택한다.
1. `pairwise_f1` 하락 금지
2. `overmerged_group_count` 증가 금지
3. `oversplit_group_count`가 늘더라도 원인 케이스를 설명할 수 있어야 함
4. 대표 샘플 케이스에서 과병합이 새로 생기면 채택 금지
5. 고정 골든셋에서 accepted row 수를 임의로 줄이지 않는다
6. auxiliary / 대행 / 관리 / 평가 용역 제외 규칙은 골든셋과 같이 검토한다

## 다음 단계
1. 현재 `v1` 골든셋을 유지한 채 애매한 singleton / 과병합 위험 샘플을 `v2` 후보셋으로 확장
2. grouping 평가를 배포 전 체크리스트와 연결
3. related notice score 조정 전후를 같은 고정 골든셋으로 비교
