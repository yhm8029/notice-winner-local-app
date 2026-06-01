from __future__ import annotations

from datetime import date
from uuid import uuid4

from backend.services.sales_action_recommendations import ACTION_LABEL_BID_RENOTICE
from backend.services.sales_action_recommendations import ACTION_LABEL_LATE_REFERENCE
from backend.services.sales_action_recommendations import ACTION_LABEL_NEW_TRACKING
from backend.services.sales_action_recommendations import ACTION_LABEL_RECHECK
from backend.services.sales_action_recommendations import ACTION_LABEL_STAGE_CHANGE
from backend.services.sales_action_recommendations import build_sales_action_recommendations
from backend.services.sales_action_recommendations import classify_sales_notice
from backend.services.sales_action_recommendations import parse_building_automation_amount_low_krw


NOW = date(2026, 5, 2)


def _row(
    *,
    project_name: str = "OO학교 복합시설 건립 설계공모",
    amount: str = "2.5억원",
    notice_date: str = "2026-04-25",
    architect_office: str = "",
    project_id: str | None = None,
    entry_id: str | None = None,
) -> dict[str, object]:
    return {
        "id": entry_id or str(uuid4()),
        "project_id": project_id or str(uuid4()),
        "project_name": project_name,
        "building_automation_estimated_amount": amount,
        "notice_date": notice_date,
        "architect_office": architect_office,
        "source_bid_no": "R26BK00000001",
        "source_bid_ord": "000",
        "demand_org_name": "OO교육청",
    }


def test_amount_range_uses_low_amount_for_business_filtering() -> None:
    assert parse_building_automation_amount_low_krw("4.67억~6.23억") == 467_000_000
    assert parse_building_automation_amount_low_krw("금50,000,000원") == 50_000_000


def test_new_design_contest_below_two_eok_is_not_new_tracking_target() -> None:
    recommendations = build_sales_action_recommendations(
        [_row(amount="1.5억원", notice_date="2026-04-28")],
        today=NOW,
    )

    assert not recommendations


def test_new_design_contest_above_two_eok_is_new_tracking_target() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                amount="2.5억원",
                notice_date="2026-04-28",
            )
            | {
                "gross_area_scale": "8,000㎡",
                "construction_cost": "311.4억원",
                "demand_contact": "노인복지과/043-850-6823",
                "site_location_1": "충청북도",
                "site_location_2": "충주시",
                "construction_start_date": "착수일로부터210일",
                "opening_scheduled_date": "20260519",
            }
        ],
        today=NOW,
    )

    assert len(recommendations) == 1
    assert recommendations[0]["primary_label"] == ACTION_LABEL_NEW_TRACKING
    assert "sort_score" not in recommendations[0]
    assert "internal_sort_score" not in recommendations[0]
    assert "최근 등록된 고액 설계공모입니다." in recommendations[0]["reasons"]
    assert recommendations[0]["tracker_entry"]["gross_area_scale"] == "8,000㎡"
    assert recommendations[0]["tracker_entry"]["construction_cost"] == "311.4억원"
    assert recommendations[0]["tracker_entry"]["demand_contact"] == "노인복지과/043-850-6823"
    assert recommendations[0]["tracker_entry"]["site_location_2"] == "충주시"


def test_internal_sort_score_is_exposed_only_when_requested() -> None:
    default_items = build_sales_action_recommendations(
        [_row(amount="2.5억원", notice_date="2026-04-28")],
        today=NOW,
    )
    admin_items = build_sales_action_recommendations(
        [_row(amount="2.5억원", notice_date="2026-04-28")],
        today=NOW,
        expose_internal_score=True,
    )

    assert "internal_sort_score" not in default_items[0]
    assert isinstance(admin_items[0]["internal_sort_score"], int)
    assert admin_items[0]["internal_sort_score"] > 0


def test_recent_execution_design_service_notice_is_stage_change() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO도서관 신축사업 실시설계 용역",
                amount="2.8억원",
                notice_date="2026-04-27",
            )
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_STAGE_CHANGE
    assert recommendations[0]["latest_meaningful_notice_type"] == "실시설계 / 설계용역"


def test_later_meaningful_followup_replaces_old_recheck_for_same_project() -> None:
    project_id = str(uuid4())
    recommendations = build_sales_action_recommendations(
        [
            _row(project_id=project_id, amount="3.2억원", notice_date="2026-01-31"),
            _row(
                project_id=project_id,
                project_name="OO도서관 신축사업 실시설계 용역",
                amount="3.2억원",
                notice_date="2026-04-27",
            ),
        ],
        today=NOW,
    )

    assert len(recommendations) == 1
    assert recommendations[0]["primary_label"] == ACTION_LABEL_STAGE_CHANGE


def test_execution_design_correction_notice_is_not_stage_change() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO도서관 신축사업 실시설계 용역 정정공고",
                amount="2.8억원",
                notice_date="2026-04-27",
            )
        ],
        today=NOW,
    )

    assert not any(ACTION_LABEL_STAGE_CHANGE in item["action_labels"] for item in recommendations)


def test_design_contest_after_ninety_one_days_without_followup_needs_recheck() -> None:
    recommendations = build_sales_action_recommendations(
        [_row(amount="3.2억원", notice_date="2026-01-31")],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_RECHECK
    assert recommendations[0]["elapsed_days"] == 91
    assert "설계공모 이후 90일 이상 후속공고가 없습니다." in recommendations[0]["reasons"]


def test_minor_change_does_not_refresh_last_meaningful_notice_date() -> None:
    project_id = str(uuid4())
    recommendations = build_sales_action_recommendations(
        [
            _row(project_id=project_id, amount="3.2억원", notice_date="2026-01-31"),
            _row(
                project_id=project_id,
                project_name="OO학교 복합시설 건립 설계공모 정정공고",
                amount="3.2억원",
                notice_date="2026-04-30",
            ),
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_RECHECK
    assert recommendations[0]["latest_meaningful_notice_date"] == "2026-01-31"
    assert recommendations[0]["elapsed_days"] == 91


def test_winner_result_after_sixty_one_days_without_followup_needs_recheck() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO복합문화센터 건립 설계공모 심사결과",
                amount="3.2억원",
                notice_date="2026-03-02",
            )
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_RECHECK
    assert recommendations[0]["elapsed_days"] == 61


def test_execution_design_after_one_hundred_days_is_not_recheck() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO복합문화센터 건립 실시설계 용역",
                amount="3.2억원",
                notice_date="2026-01-22",
            )
        ],
        today=NOW,
    )

    assert not any(ACTION_LABEL_RECHECK in item["action_labels"] for item in recommendations)


def test_execution_design_after_one_hundred_eighty_one_days_is_recheck() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO복합문화센터 건립 실시설계 용역",
                amount="3.2억원",
                notice_date="2025-11-02",
            )
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_RECHECK


def test_construction_bid_after_thirty_one_days_is_recheck() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO복합문화센터 건립 공사입찰",
                amount="3.2억원",
                notice_date="2026-04-01",
            )
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_RECHECK


def test_construction_bid_renotice_gets_failed_bid_label() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO복합문화센터 건립 공사입찰 재공고",
                amount="2.5억원",
                notice_date="2026-04-30",
            )
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_BID_RENOTICE
    assert "공사입찰 재공고가 확인되었습니다." in recommendations[0]["reasons"]


def test_late_supervision_stage_gets_reference_label() -> None:
    recommendations = build_sales_action_recommendations(
        [
            _row(
                project_name="OO복합문화센터 건립 감리 용역",
                amount="2.5억원",
                notice_date="2026-01-01",
            )
        ],
        today=NOW,
    )

    assert recommendations[0]["primary_label"] == ACTION_LABEL_LATE_REFERENCE


def test_cancelled_withdrawn_or_stopped_notice_is_excluded() -> None:
    recommendations = build_sales_action_recommendations(
        [_row(project_name="OO복합문화센터 건립 설계공모 취소공고", amount="5억원")],
        today=NOW,
    )

    assert recommendations == []
    assert classify_sales_notice("OO복합문화센터 건립 설계공모 중지공고").is_excluded


def test_under_fifty_million_is_excluded_from_default_recommendations() -> None:
    recommendations = build_sales_action_recommendations(
        [_row(project_name="OO복합문화센터 건립 실시설계 용역", amount="0.49억원")],
        today=NOW,
    )

    assert recommendations == []


def test_same_project_same_label_is_suppressed_within_seven_days() -> None:
    project_id = str(uuid4())
    recommendations = build_sales_action_recommendations(
        [_row(project_id=project_id, amount="2.5억원", notice_date="2026-04-28")],
        today=NOW,
        recent_label_exposures={(project_id, ACTION_LABEL_NEW_TRACKING): date(2026, 4, 30)},
    )

    assert recommendations == []


def test_stage_change_recommendations_are_limited_to_five_per_day() -> None:
    rows = [
        _row(
            project_name=f"OO센터 {index} 실시설계 용역",
            amount=f"{2 + index}.0억원",
            notice_date="2026-04-30",
        )
        for index in range(8)
    ]

    recommendations = build_sales_action_recommendations(rows, today=NOW)

    stage_items = [item for item in recommendations if item["primary_label"] == ACTION_LABEL_STAGE_CHANGE]
    assert len(stage_items) == 5
    assert stage_items[0]["automation_amount_low_krw"] > stage_items[-1]["automation_amount_low_krw"]
