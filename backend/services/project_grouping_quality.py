from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Any


@dataclass(frozen=True)
class GroupingAssignment:
    item_key: str
    expected_group_id: str
    predicted_group_id: str
    project_name: str = ""
    bid_no: str = ""
    bid_ord: str = ""


def _pairwise_links(group_to_items: dict[str, list[str]]) -> set[tuple[str, str]]:
    links: set[tuple[str, str]] = set()
    for item_keys in group_to_items.values():
        unique_items = sorted({str(item).strip() for item in item_keys if str(item).strip()})
        if len(unique_items) < 2:
            continue
        for left, right in combinations(unique_items, 2):
            links.add((left, right))
    return links


def _group_to_items(
    assignments: list[GroupingAssignment],
    *,
    attr_name: str,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for assignment in assignments:
        group_id = str(getattr(assignment, attr_name) or "").strip()
        item_key = str(assignment.item_key or "").strip()
        if not group_id or not item_key:
            continue
        grouped[group_id].append(item_key)
    return grouped


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def evaluate_project_grouping(assignments: list[GroupingAssignment]) -> dict[str, Any]:
    expected_groups = _group_to_items(assignments, attr_name="expected_group_id")
    predicted_groups = _group_to_items(assignments, attr_name="predicted_group_id")

    expected_pairs = _pairwise_links(expected_groups)
    predicted_pairs = _pairwise_links(predicted_groups)
    true_positive_pairs = expected_pairs & predicted_pairs

    precision = _safe_ratio(len(true_positive_pairs), len(predicted_pairs))
    recall = _safe_ratio(len(true_positive_pairs), len(expected_pairs))
    f1 = _safe_ratio(2 * precision * recall, precision + recall) if precision and recall else 0.0

    by_item_key = {assignment.item_key: assignment for assignment in assignments}

    overmerged_groups: list[dict[str, Any]] = []
    for predicted_group_id, item_keys in sorted(predicted_groups.items()):
        expected_group_ids = sorted(
            {
                str(by_item_key[item_key].expected_group_id or "").strip()
                for item_key in item_keys
                if item_key in by_item_key
            }
        )
        expected_group_ids = [value for value in expected_group_ids if value]
        if len(expected_group_ids) <= 1:
            continue
        overmerged_groups.append(
            {
                "predicted_group_id": predicted_group_id,
                "expected_group_ids": expected_group_ids,
                "item_keys": sorted(item_keys),
                "item_count": len(item_keys),
            }
        )

    oversplit_groups: list[dict[str, Any]] = []
    for expected_group_id, item_keys in sorted(expected_groups.items()):
        predicted_group_ids = sorted(
            {
                str(by_item_key[item_key].predicted_group_id or "").strip()
                for item_key in item_keys
                if item_key in by_item_key
            }
        )
        predicted_group_ids = [value for value in predicted_group_ids if value]
        if len(predicted_group_ids) <= 1:
            continue
        oversplit_groups.append(
            {
                "expected_group_id": expected_group_id,
                "predicted_group_ids": predicted_group_ids,
                "item_keys": sorted(item_keys),
                "item_count": len(item_keys),
            }
        )

    item_rows = [
        {
            "item_key": assignment.item_key,
            "bid_no": assignment.bid_no,
            "bid_ord": assignment.bid_ord,
            "project_name": assignment.project_name,
            "expected_group_id": assignment.expected_group_id,
            "predicted_group_id": assignment.predicted_group_id,
            "matched": assignment.expected_group_id == assignment.predicted_group_id,
        }
        for assignment in assignments
    ]

    return {
        "item_count": len(assignments),
        "expected_group_count": len(expected_groups),
        "predicted_group_count": len(predicted_groups),
        "pairwise_precision": round(precision, 6),
        "pairwise_recall": round(recall, 6),
        "pairwise_f1": round(f1, 6),
        "expected_pair_count": len(expected_pairs),
        "predicted_pair_count": len(predicted_pairs),
        "true_positive_pair_count": len(true_positive_pairs),
        "overmerged_group_count": len(overmerged_groups),
        "oversplit_group_count": len(oversplit_groups),
        "overmerged_groups": overmerged_groups,
        "oversplit_groups": oversplit_groups,
        "items": item_rows,
    }
