from __future__ import annotations

import json

from scripts.reconcile_backup_artifacts import normalize_path_for_match
from scripts.reconcile_backup_artifacts import reconcile_artifacts
from scripts.reconcile_backup_artifacts import write_reconciliation_report


def test_normalize_path_for_match_handles_slashes_and_relative_prefixes():
    assert normalize_path_for_match("\\output\\artifacts\\a.xlsx") == "output/artifacts/a.xlsx"
    assert normalize_path_for_match("/home/ubuntu/app/output/artifacts/a.xlsx").endswith("output/artifacts/a.xlsx")


def test_reconcile_artifacts_matches_suffix_paths():
    artifacts = [
        {"id": "a1", "storage_path": "output/artifacts/a.xlsx"},
        {"id": "a2", "storage_path": "output/artifacts/missing.xlsx"},
    ]
    ec2_files = [
        {"path": "/home/ubuntu/app/output/artifacts/a.xlsx", "size_bytes": 12, "modified_at": "2026"},
    ]

    report = reconcile_artifacts(artifacts, ec2_files)

    assert report["artifact_count"] == 2
    assert report["matched_count"] == 1
    assert report["missing_count"] == 1
    assert report["missing"][0]["id"] == "a2"


def test_write_reconciliation_report_writes_json(tmp_path):
    report = {"artifact_count": 1, "matched_count": 1, "missing_count": 0, "matched": [], "missing": []}

    write_reconciliation_report(tmp_path, report)

    assert json.loads((tmp_path / "artifact_reconciliation.json").read_text(encoding="utf-8"))["artifact_count"] == 1
