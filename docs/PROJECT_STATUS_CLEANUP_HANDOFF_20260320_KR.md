현재 기준
- 코드 최신 기준 브랜치: `feature/related-notice-search`
- 기능 반영 커밋: `00f8cee`

이번까지 완료한 것
- 프로젝트 현황 `엑셀/CSV 다운로드` 추가
- 연관공고 프런트 prefetch + 서버 응답 캐시 추가
- 연관공고 aggregate fallback 보강
- `architect_office`에서 `native_web` fallback 제거
- `LOFIN core query` 및 `ctrt_knd_nm=용역` 보강
- 관련 테스트 통과 상태 확인

DB 정리 완료
- 오염 부모 run 삭제:
  - `cc60f73e-8f35-49bc-af5d-b74204982e2e`
- 오염 child tracker_export 삭제:
  - `34960c75-9f68-4580-86e9-74e6276b210b`
- 오염 tracker rows 삭제:
  - `source_tracker_run_id = 34960c75-9f68-4580-86e9-74e6276b210b`
  - 삭제 수: `47`
- 함께 삭제한 DB 흔적:
  - `pipeline_runs`
  - `pipeline_logs`
  - `run_artifacts`

정리 후 확인
- 프로젝트 현황 기준 오염 키워드 재확인:
  - `수학여행`
  - `방역소독`
  - `위탁용역`
- 현재 visible contaminated count: `0`

오염 원인 요약
- 현재 검색 로직이 즉시 오염시키는 문제가 아니라,
  예전에 생성된 잘못된 run이 tracker rows로 남아 있었음
- 특히 아래 부모 run은 `notice_title`이 `????`로 깨진 상태에서 성공했고,
  child `tracker_export`가 오염 tracker rows를 생성했음

다음 작업
1. 브라우저 강력 새로고침 후 프로젝트 현황이 실제로 깨끗한지 최종 확인
2. `notice_title = ????` 같은 깨진 run이 다시 생기는지 원인 추적
3. 재발 시 관리자용 정리 루트 추가 검토
   - source tracker run 기준 삭제
   - 부모/child run/log/artifact 일괄 정리
4. 필요하면 오염 run 생성 방지 가드 검토
   - 단, 사용자가 다른 키워드 검색도 해야 하므로 `설계공모 전용 가드`는 아직 보류
