# CONTACT_RESOLVER_V1 Next Steps

기준 커밋
- 브랜치: `feature/related-notice-search`
- 구현 커밋: `0a59728`

현재 상태
- `demand_contact` observation/resolver v1을 export 경로에 연결함
- `review` 상태 연락처는 seed fallback으로 채우지 않고 빈값 유지함
- LLM contact는 최종 `demand_contact`로 직접 반영하지 않음
- 라벨링 시드 `49건` 결과를 저장소에 포함함

아직 반드시 해야 하는 것
1. EC2 반영
- 현재 브랜치 최신 커밋을 EC2 운영 서버에 배포해야 함
- `notice-winner-pipeline-web.service` 재시작까지 확인 필요

2. 샘플 재추출 검증
- 대표 오염/blank 샘플을 다시 추출해서
  - `resolved`
  - `review`
  - `no_owner_candidate`
  분포와 실제 결과를 확인해야 함

3. 백필 검증
- resolver v1 기준으로 기존 tracker 데이터에 대해
  - 안전하게 교정 가능한 항목
  - review로 남겨야 하는 항목
  을 나눠서 백필 효과를 검증해야 함

권장 순서
1. EC2 반영
2. 대표 샘플 재추출
3. 백필 dry-run 검증
4. 실제 백필 여부 결정

메모
- 현재 저장소에 포함된 아래 파일은 테스트/검증용 임시 파일이므로 검증 종료 후 삭제 여부를 판단해야 함
  - `scripts/debug_tracker_project_grouping.py`
  - `tmp_deploy_f1fb54e.tar.gz`
  - `output/debug/contact_labeling_seed_20260327_153832_labeled_v1.csv`
  - `output/debug/contact_labeling_seed_20260327_153832_labeled_v1.xlsx`
