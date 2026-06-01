from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any
from uuid import UUID

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.repositories import ArtifactRepositoryError
from backend.repositories import TrackerEntryRepositoryError
from backend.repositories import get_artifact_repository
from backend.repositories import get_tracker_entry_repository
from backend.services.artifact_files import resolve_artifact_path
from backend.services.attachment_text_extract import download_attachment_text_with_timing
from backend.services.native_gui_rules import extract_contact_from_notice_text
from backend.services.native_gui_rules import extract_notice_area_value
from backend.services.native_gui_rules import extract_notice_cost_won
from backend.services.notice_file_view_backend import select_primary_notice_attachment
from backend.services.synap_text_extract import download_notice_attachment_text_via_synap

SEED_ARTIFACT_TYPE = "seed_csv"
TRACKER_PAGE_SIZE = 100


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare current attachment parsing vs Synap XML text layer.")
    parser.add_argument("--sample-limit", type=int, default=5, help="Number of HWP/HWPX samples to compare.")
    parser.add_argument("--page-scan-limit", type=int, default=10, help="How many tracker pages to scan for samples.")
    parser.add_argument("--max-synap-pages", type=int, default=30, help="Maximum Synap pages to read per document.")
    parser.add_argument("--output", type=Path, default=Path(".tmp-synap-text-layer-compare.json"))
    args = parser.parse_args()

    tracker_repository = get_tracker_entry_repository()
    artifact_repository = get_artifact_repository()

    compared: list[dict[str, Any]] = []
    seed_row_cache: dict[str, list[dict[str, str]]] = {}
    for page_no in range(1, max(1, args.page_scan_limit) + 1):
        try:
            entries, _ = tracker_repository.list_entries(
                page=page_no,
                page_size=TRACKER_PAGE_SIZE,
                q="",
                region="",
                exclude_auxiliary_titles=True,
                edited_only=False,
                source_run_id=None,
                source_tracker_run_id=None,
                sheet_name="",
                section_name="",
            )
        except TrackerEntryRepositoryError as exc:
            raise SystemExit(f"tracker entries load failed: {exc}") from exc
        if not entries:
            break
        for entry in entries:
            sample = _build_comparison_row(entry, artifact_repository=artifact_repository, seed_row_cache=seed_row_cache, max_synap_pages=args.max_synap_pages)
            if sample is None:
                continue
            compared.append(sample)
            if len(compared) >= max(1, args.sample_limit):
                break
        if len(compared) >= max(1, args.sample_limit):
            break

    summary = _summarize_results(compared)
    payload = {"summary": summary, "items": compared}
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def _build_comparison_row(
    entry: dict[str, Any],
    *,
    artifact_repository: Any,
    seed_row_cache: dict[str, list[dict[str, str]]],
    max_synap_pages: int,
) -> dict[str, Any] | None:
    source_run_id = entry.get("source_run_id")
    if not source_run_id:
        return None
    source_row = _select_source_notice_row(
        entry,
        artifact_repository=artifact_repository,
        seed_row_cache=seed_row_cache,
    )
    if not source_row:
        return None

    attachment = select_primary_notice_attachment(source_row)
    attachment_url = str(attachment.get("url") or "").strip()
    file_name = str(attachment.get("file_name") or "").strip()
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".hwp", ".hwpx"}:
        return None

    current_result = download_attachment_text_with_timing(url=attachment_url, file_name=file_name)
    synap_result = download_notice_attachment_text_via_synap(
        bid_no=str(source_row.get("bid_no") or entry.get("source_bid_no") or "").strip(),
        bid_ord=str(source_row.get("bid_ord") or entry.get("source_bid_ord") or "000").strip() or "000",
        attachment_url=attachment_url,
        unty_atch_file_no=str(
            source_row.get("item_pbanc_unty_atch_file_no")
            or source_row.get("itemPbancUntyAtchFileNo")
            or ""
        ).strip(),
        max_pages=max_synap_pages,
    )

    project_name = str(entry.get("project_name") or source_row.get("project_name") or "").strip()
    org_name = str(source_row.get("org_name") or source_row.get("demand_org_name") or "").strip()
    current_text = str(current_result.text or "").strip()
    synap_text = str(synap_result.text or "").strip()
    return {
        "entry_id": str(entry.get("id") or ""),
        "bid_no": str(source_row.get("bid_no") or entry.get("source_bid_no") or "").strip(),
        "bid_ord": str(source_row.get("bid_ord") or entry.get("source_bid_ord") or "000").strip() or "000",
        "project_name": project_name,
        "file_name": file_name,
        "attachment_url": attachment_url,
        "current_text_length": len(current_text),
        "synap_text_length": len(synap_text),
        "synap_page_count": int(synap_result.page_count or 0),
        "current_contact": extract_contact_from_notice_text(current_text, org_name),
        "synap_contact": extract_contact_from_notice_text(synap_text, org_name),
        "current_area": extract_notice_area_value(current_text, project_name=project_name),
        "synap_area": extract_notice_area_value(synap_text, project_name=project_name),
        "current_cost": str(extract_notice_cost_won(current_text) or ""),
        "synap_cost": str(extract_notice_cost_won(synap_text) or ""),
        "current_preview": current_text[:800],
        "synap_preview": synap_text[:800],
    }


def _select_source_notice_row(
    entry: dict[str, Any],
    *,
    artifact_repository: Any,
    seed_row_cache: dict[str, list[dict[str, str]]],
) -> dict[str, str] | None:
    source_run_id = entry.get("source_run_id")
    if source_run_id is None:
        return None
    run_key = str(source_run_id)
    seed_rows = seed_row_cache.get(run_key)
    if seed_rows is None:
        try:
            artifacts = artifact_repository.list_artifacts(run_id=UUID(run_key))
        except ArtifactRepositoryError:
            return None
        seed_rows = []
        for artifact in artifacts:
            if str(artifact.get("artifact_type") or "").strip() != SEED_ARTIFACT_TYPE:
                continue
            storage_path = str(artifact.get("storage_path") or "").strip()
            if not storage_path:
                continue
            artifact_path = resolve_artifact_path(storage_path)
            if not artifact_path.exists():
                continue
            with artifact_path.open("r", encoding="utf-8-sig", newline="") as fp:
                reader = csv.DictReader(fp)
                seed_rows.extend({key: str(value or "").strip() for key, value in row.items()} for row in reader)
        seed_row_cache[run_key] = seed_rows

    target_bid_no = str(entry.get("source_bid_no") or "").strip().upper()
    target_bid_ord = str(entry.get("source_bid_ord") or "000").strip() or "000"
    if not target_bid_no:
        return None
    for row in seed_rows:
        bid_no = str(row.get("bid_no") or "").strip().upper()
        bid_ord = str(row.get("bid_ord") or "000").strip() or "000"
        if bid_no == target_bid_no and bid_ord == target_bid_ord:
            return row
    return None


def _summarize_results(items: list[dict[str, Any]]) -> dict[str, Any]:
    def _nonempty(value: str) -> bool:
        return bool(str(value or "").strip())

    return {
        "compared_count": len(items),
        "synap_nonempty_text": sum(1 for item in items if item["synap_text_length"] > 0),
        "current_nonempty_text": sum(1 for item in items if item["current_text_length"] > 0),
        "contact_improved": sum(1 for item in items if not _nonempty(item["current_contact"]) and _nonempty(item["synap_contact"])),
        "area_improved": sum(1 for item in items if not _nonempty(item["current_area"]) and _nonempty(item["synap_area"])),
        "cost_improved": sum(1 for item in items if not _nonempty(item["current_cost"]) and _nonempty(item["synap_cost"])),
        "longer_text_count": sum(1 for item in items if int(item["synap_text_length"]) > int(item["current_text_length"])),
    }


if __name__ == "__main__":
    raise SystemExit(main())
