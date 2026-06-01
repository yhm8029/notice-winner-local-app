from __future__ import annotations

import unittest
from datetime import datetime
from datetime import timezone
from uuid import uuid4

from backend.services.tracker_entry_snapshot_backend import hydrate_tracker_entry_detail_row
from backend.services.tracker_entry_snapshot_backend import hydrate_tracker_entry_export_rows
from backend.services.tracker_entry_snapshot_backend import hydrate_tracker_entry_summary_rows
from backend.services.tracker_entry_snapshot_backend import is_tracker_entry_snapshot_fresh
from backend.services.tracker_entry_snapshot_backend import materialize_tracker_entry_snapshot_views
from backend.services.tracker_entry_snapshot_backend import normalize_tracker_entry_presentation


class TrackerEntrySnapshotBackendTests(unittest.TestCase):
    def test_normalize_tracker_entry_presentation_repairs_existing_site_city_noise_examples(self) -> None:
        cases = [
            {
                "project_name": "(집행대행)구펑초등학교 교사동 공간재구조화사업 설계공모",
                "demand_org_name": "경상북도교육청",
                "client_location": "경상북도교육청",
                "site_location_1": "경상북도",
                "site_location_2": "공간재구",
                "expected": ("경상북도", ""),
            },
            {
                "project_name": "현산면 기초생활거점조성사업 세부설계용역 건축설계공모",
                "demand_org_name": "한국농어촌공사 전남지역본부 해남.완도지사",
                "client_location": "한국농어촌공사 전남지역본부 해남.완도지사",
                "site_location_1": "",
                "site_location_2": "과업지시",
                "expected": ("전라남도", ""),
            },
            {
                "project_name": "정읍제일고 학교복합문화센터 건립 설계공모",
                "demand_org_name": "전북특별자치도교육청 전북특별자치도정읍교육지원청",
                "client_location": "전북특별자치도교육청 전북특별자치도정읍교육지원청",
                "site_location_1": "전북특별자치도",
                "site_location_2": "전북특별자치도정읍",
                "expected": ("전북특별자치도", "정읍시"),
            },
            {
                "project_name": "로봇드론지원센터 조성사업 기본 및 실시설계 용역 설계공모",
                "demand_org_name": "대전광역시 건설관리본부",
                "client_location": "대전광역시 건설관리본부",
                "site_location_1": "대전광역시",
                "site_location_2": "입면",
                "expected": ("대전광역시", ""),
            },
            {
                "project_name": "고창 동학농민혁명 성지화 사업 기본 및 실시설계 공모 제안서 제출 안내",
                "demand_org_name": "전북특별자치도 고창군",
                "client_location": "전북특별자치도 고창군",
                "site_location_1": "전북특별자치도",
                "site_location_2": "요구",
                "expected": ("전북특별자치도", "고창군"),
            },
        ]

        cases.extend(
            [
                {
                    "project_name": "\ubd88\ub85c\ub3d9 \ud788\ud2b8 \uc870\uc131\uc0ac\uc5c5 \uae30\ubcf8 \ubc0f \uc2e4\uc2dc\uc124\uacc4\uc6a9\uc5ed \uac74\ucd95\uc124\uacc4\uacf5\ubaa8(\uac04\uc774\uacf5\ubaa8)",
                    "demand_org_name": "\ub300\uad6c\uad11\uc5ed\uc2dc \ub3d9\uad6c",
                    "client_location": "\ub300\uad6c\uad11\uc5ed\uc2dc \ub3d9\uad6c",
                    "site_location_1": "\ub300\uad6c\uad11\uc5ed\uc2dc",
                    "site_location_2": "\ub300\uad6c\uad11\uc5ed\uc2dc",
                    "expected": ("\ub300\uad6c\uad11\uc5ed\uc2dc", "\ub3d9\uad6c"),
                },
                {
                    "project_name": "\uc870\uc6d01\ub3d9 \ubcf5\ud569\ubb38\ud654\uc13c\ud130 \uac74\ucd95 \uc124\uacc4\uacf5\ubaa8",
                    "demand_org_name": "\uacbd\uae30\ub3c4 \uc218\uc6d0\uc2dc \uc7a5\uc548\uad6c",
                    "client_location": "\uacbd\uae30\ub3c4 \uc218\uc6d0\uc2dc \uc7a5\uc548\uad6c",
                    "site_location_1": "\uacbd\uae30\ub3c4",
                    "site_location_2": "\uc218\uc6d0\uc2dc",
                    "expected": ("\uacbd\uae30\ub3c4", "\uc7a5\uc548\uad6c"),
                },
            ]
        )

        for case in cases:
            with self.subTest(project_name=case["project_name"]):
                normalized = normalize_tracker_entry_presentation(
                    {
                        "project_name": case["project_name"],
                        "construction_cost": "10억원",
                        "building_automation_estimated_amount": "",
                        "last_checked_date": "20260406",
                        "construction_start_date": "",
                        "demand_org_name": case["demand_org_name"],
                        "client_location": case["client_location"],
                        "site_location_1": case["site_location_1"],
                        "site_location_2": case["site_location_2"],
                    },
                    winner_row=None,
                )
                self.assertEqual(
                    (normalized["site_location_1"], normalized["site_location_2"]),
                    case["expected"],
                )

    def test_is_tracker_entry_snapshot_fresh_compares_updated_at(self) -> None:
        snapshot = {"updated_at": "2026-03-29T10:00:00+00:00"}
        row = {"updated_at": "2026-03-29T09:00:00+00:00", "created_at": "2026-03-29T08:00:00+00:00"}

        self.assertTrue(
            is_tracker_entry_snapshot_fresh(
                snapshot,
                row,
                parse_iso_datetime_fn=lambda value: datetime.fromisoformat(str(value)),
            )
        )

    def test_materialize_tracker_entry_snapshot_views_builds_summary_detail_export_and_snapshot(self) -> None:
        entry_id = uuid4()
        now = datetime(2026, 3, 29, 12, 0, tzinfo=timezone.utc)
        rows = [
            {
                "id": entry_id,
                "project_name": "테스트 프로젝트",
                "construction_cost": "10.0억원",
                "updated_at": "",
                "created_at": "",
            }
        ]

        materialized = materialize_tracker_entry_snapshot_views(
            rows,
            annotate_tracker_entries_with_project_refs_fn=lambda value: [
                {**item, "project_id": uuid4()} for item in value
            ],
            annotate_tracker_entries_with_opening_dates_fn=lambda value: [
                {**item, "opening_scheduled_date": "2026-04-01"} for item in value
            ],
            annotate_tracker_entries_with_field_diagnostics_fn=lambda value: [
                {**item, "field_diagnostics": [{"field_key": "construction_cost"}]} for item in value
            ],
            normalize_tracker_rows_for_presentation_fn=lambda value: value,
            coerce_uuid_or_none_fn=lambda value: value if str(value or "").strip() else None,
            model_to_json_dict_fn=lambda model: dict(model),
            to_tracker_entry_summary_model_fn=lambda row: row,
            to_tracker_entry_model_fn=lambda row: row,
            tracking_export_fieldnames=("project_name", "construction_cost"),
            utc_now_fn=lambda: now,
        )

        item = materialized[str(entry_id)]
        self.assertEqual(item["summary_row"]["opening_scheduled_date"], "2026-04-01")
        self.assertEqual(item["detail_row"]["field_diagnostics"], [{"field_key": "construction_cost"}])
        self.assertEqual(
            item["export_row"],
            {"project_name": "테스트 프로젝트", "construction_cost": "10.0억원"},
        )
        self.assertEqual(item["snapshot"]["tracker_entry_id"], entry_id)
        self.assertEqual(item["snapshot"]["updated_at"], now)

    def test_hydrate_tracker_entry_summary_rows_merges_raw_metadata_with_summary_json(self) -> None:
        entry_id = uuid4()
        rows = [
            {
                "id": entry_id,
                "row_no": 7,
                "updated_at": "2026-03-29T10:00:00+00:00",
                "overridden_fields": ["construction_cost"],
                "project_name": "원본",
            }
        ]

        hydrated = hydrate_tracker_entry_summary_rows(
            organization_id=uuid4(),
            rows=rows,
            load_tracker_entry_snapshot_map_fn=lambda **_: {
                str(entry_id): {
                    "tracker_entry_id": entry_id,
                    "updated_at": "2026-03-29T10:00:00+00:00",
                    "summary_json": {"project_name": "요약", "construction_cost": "12.4억원"},
                }
            },
            is_tracker_entry_snapshot_fresh_fn=lambda snapshot, row: True,
            upsert_tracker_entry_snapshots_best_effort_fn=lambda **_: {},
        )

        self.assertEqual(hydrated[0]["project_name"], "요약")
        self.assertEqual(hydrated[0]["row_no"], 7)
        self.assertEqual(hydrated[0]["updated_at"], "2026-03-29T10:00:00+00:00")
        self.assertEqual(hydrated[0]["overridden_fields"], ["construction_cost"])

    def test_hydrate_tracker_entry_export_rows_prefers_fresh_snapshot_export_json(self) -> None:
        entry_id = uuid4()
        rows = [{"id": entry_id, "project_name": "원본"}]

        hydrated = hydrate_tracker_entry_export_rows(
            organization_id=uuid4(),
            rows=rows,
            load_tracker_entry_snapshot_map_fn=lambda **_: {
                str(entry_id): {
                    "tracker_entry_id": entry_id,
                    "updated_at": "2026-03-29T10:00:00+00:00",
                    "export_json": {"project_name": "내보내기"},
                }
            },
            is_tracker_entry_snapshot_fresh_fn=lambda snapshot, row: True,
            upsert_tracker_entry_snapshots_best_effort_fn=lambda **_: {},
        )

        self.assertEqual(hydrated, [{"project_name": "내보내기"}])

    def test_hydrate_tracker_entry_detail_row_uses_materialized_detail_when_snapshot_missing(self) -> None:
        entry_id = uuid4()
        row = {"id": entry_id, "project_name": "원본"}

        hydrated = hydrate_tracker_entry_detail_row(
            organization_id=uuid4(),
            row=row,
            load_tracker_entry_snapshot_map_fn=lambda **_: {},
            is_tracker_entry_snapshot_fresh_fn=lambda snapshot, current_row: False,
            upsert_tracker_entry_snapshots_best_effort_fn=lambda **_: {
                str(entry_id): {"detail_row": {"project_name": "상세"}}
            },
        )

        self.assertEqual(hydrated, {"project_name": "상세"})


if __name__ == "__main__":
    unittest.main()
