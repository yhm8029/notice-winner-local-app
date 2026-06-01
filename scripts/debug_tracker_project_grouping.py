from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID
from uuid import uuid5

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.api.app import PROJECT_NAMESPACE
from backend.api.app import _derive_tracker_entry_project_identity
from backend.api.app import _norm_text
from backend.api.app import _select_project_search_name
from backend.api.app import _strip_project_notice_noise
from backend.repositories.factory import get_tracker_entry_repository
from backend.repositories.factory import reset_tracker_entry_repository
from backend.repositories.tracker_entries import TrackerEntryRepository
from backend.repositories.tracker_entries import TrackerEntryRepositoryError

REPORT_FIELDS = (
    "loose_bucket",
    "bucket_title",
    "bucket_row_count",
    "bucket_distinct_project_keys",
    "split_group_flag",
    "derived_project_id",
    "project_key",
    "project_search_name",
    "entry_id",
    "entry_key",
    "source_bid_no",
    "source_bid_ord",
    "source_project_name_norm",
    "project_name",
    "demand_org_name",
    "site_location_1",
    "site_location_2",
    "architect_office",
    "demand_contact",
    "architect_office_source",
    "demand_contact_source",
    "overridden_fields",
    "has_overrides",
    "notice_date",
    "updated_at",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find tracker rows that look like the same project but currently split into different project groups."
    )
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--page-size", type=int, default=500)
    parser.add_argument("--q", default="", help="Optional project-name substring filter before grouping.")
    parser.add_argument(
        "--split-only",
        action="store_true",
        help="Only include duplicate title buckets that currently map to 2+ distinct project keys.",
    )
    parser.add_argument("--limit-buckets", type=int, default=0, help="Limit output to the first N duplicate buckets.")
    parser.add_argument("--output", default="", help="Output CSV path. Defaults under output/debug/.")
    return parser.parse_args()


def load_env_file(path: str) -> None:
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if not key:
            continue
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def _list_all_entries(*, repo: TrackerEntryRepository, page_size: int) -> list[dict[str, Any]]:
    page = 1
    rows: list[dict[str, Any]] = []
    while True:
        batch, total = repo.list_entries(
            page=page,
            page_size=page_size,
            q="",
            region="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )
        rows.extend(batch)
        if len(rows) >= total or not batch:
            return rows
        page += 1


def _fetch_source_field_map(repo: TrackerEntryRepository, entry_ids: list[str]) -> dict[str, dict[str, str]]:
    request_json = getattr(repo, "_request_json", None)
    config = getattr(repo, "_config", None)
    if request_json is None or config is None or not getattr(config, "organization_id", None):
        return {}
    out: dict[str, dict[str, str]] = {}
    chunk_size = 100
    for idx in range(0, len(entry_ids), chunk_size):
        chunk = [item for item in entry_ids[idx : idx + chunk_size] if item]
        if not chunk:
            continue
        try:
            rows, _headers = request_json(
                method="GET",
                path="/tracker_entries",
                query=[
                    ("select", "id,demand_contact_source,architect_office_source"),
                    ("organization_id", f"eq.{config.organization_id}"),
                    ("id", f"in.({','.join(chunk)})"),
                ],
            )
        except Exception:
            return out
        for row in rows:
            entry_id = str(row.get("id") or "").strip()
            if not entry_id:
                continue
            out[entry_id] = {
                "demand_contact_source": str(row.get("demand_contact_source") or "").strip(),
                "architect_office_source": str(row.get("architect_office_source") or "").strip(),
            }
    return out


def _build_loose_bucket(project_name: str, source_project_name_norm: str) -> tuple[str, str]:
    search_name = _select_project_search_name(project_name, source_project_name_norm)
    loose_title = _strip_project_notice_noise(project_name) or search_name or project_name or source_project_name_norm
    loose_bucket = _norm_text(loose_title)
    return loose_bucket, loose_title


def _output_path(path: str) -> Path:
    if path:
        return Path(path).expanduser()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return ROOT / "output" / "debug" / f"tracker_project_grouping_{stamp}.csv"


def main() -> int:
    args = parse_args()
    load_env_file(args.env_file)
    reset_tracker_entry_repository()
    repo = get_tracker_entry_repository()
    try:
        rows = _list_all_entries(repo=repo, page_size=args.page_size)
    except TrackerEntryRepositoryError as exc:
        print(f"failed to load tracker entries: {exc}", file=sys.stderr)
        return 1

    q_norm = _norm_text(args.q)
    filtered_rows: list[dict[str, Any]] = []
    for row in rows:
        project_name = str(row.get("project_name") or "").strip()
        source_project_name_norm = str(row.get("source_project_name_norm") or "").strip()
        if q_norm and q_norm not in _norm_text(" ".join((project_name, source_project_name_norm))):
            continue
        filtered_rows.append(row)

    source_map = _fetch_source_field_map(
        repo,
        [str(row.get("id") or "").strip() for row in filtered_rows],
    )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bucket_titles: dict[str, str] = {}
    for row in filtered_rows:
        project_name = str(row.get("project_name") or "").strip()
        source_project_name_norm = str(row.get("source_project_name_norm") or "").strip()
        loose_bucket, bucket_title = _build_loose_bucket(project_name, source_project_name_norm)
        if not loose_bucket:
            continue
        grouped[loose_bucket].append(row)
        bucket_titles.setdefault(loose_bucket, bucket_title)

    report_rows: list[dict[str, Any]] = []
    bucket_summaries: list[tuple[str, int, int]] = []
    for loose_bucket, bucket_rows in grouped.items():
        if len(bucket_rows) < 2:
            continue
        current_project_keys: set[str] = set()
        for row in bucket_rows:
            _project_name, project_search_name, project_key = _derive_tracker_entry_project_identity(row)
            if project_key:
                current_project_keys.add(project_key)
            elif project_search_name:
                current_project_keys.add(_norm_text(project_search_name))
        if args.split_only and len(current_project_keys) < 2:
            continue
        bucket_summaries.append((loose_bucket, len(bucket_rows), len(current_project_keys)))
        for row in bucket_rows:
            project_name, project_search_name, project_key = _derive_tracker_entry_project_identity(row)
            derived_project_id = str(uuid5(PROJECT_NAMESPACE, f"project:{project_key}")) if project_key else ""
            entry_id = str(row.get("id") or "").strip()
            source_fields = source_map.get(entry_id, {})
            report_rows.append(
                {
                    "loose_bucket": loose_bucket,
                    "bucket_title": bucket_titles.get(loose_bucket, ""),
                    "bucket_row_count": str(len(bucket_rows)),
                    "bucket_distinct_project_keys": str(len(current_project_keys)),
                    "split_group_flag": "Y" if len(current_project_keys) >= 2 else "",
                    "derived_project_id": derived_project_id,
                    "project_key": project_key,
                    "project_search_name": project_search_name,
                    "entry_id": entry_id,
                    "entry_key": str(row.get("entry_key") or "").strip(),
                    "source_bid_no": str(row.get("source_bid_no") or "").strip(),
                    "source_bid_ord": str(row.get("source_bid_ord") or "").strip(),
                    "source_project_name_norm": str(row.get("source_project_name_norm") or "").strip(),
                    "project_name": project_name,
                    "demand_org_name": str(row.get("demand_org_name") or "").strip(),
                    "site_location_1": str(row.get("site_location_1") or "").strip(),
                    "site_location_2": str(row.get("site_location_2") or "").strip(),
                    "architect_office": str(row.get("architect_office") or "").strip(),
                    "demand_contact": str(row.get("demand_contact") or "").strip(),
                    "architect_office_source": source_fields.get("architect_office_source", ""),
                    "demand_contact_source": source_fields.get("demand_contact_source", ""),
                    "overridden_fields": "|".join(str(item) for item in (row.get("overridden_fields") or [])),
                    "has_overrides": "Y" if row.get("has_overrides") else "",
                    "notice_date": str(row.get("notice_date") or "").strip(),
                    "updated_at": str(row.get("updated_at") or "").strip(),
                }
            )

    bucket_summaries.sort(key=lambda item: (item[2], item[1], item[0]), reverse=True)
    if args.limit_buckets > 0:
        allowed = {item[0] for item in bucket_summaries[: args.limit_buckets]}
        report_rows = [row for row in report_rows if row["loose_bucket"] in allowed]
        bucket_summaries = [item for item in bucket_summaries if item[0] in allowed]

    output_path = _output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(report_rows)

    print(f"tracker rows scanned: {len(filtered_rows)}")
    print(f"duplicate loose buckets: {len(bucket_summaries)}")
    for loose_bucket, row_count, key_count in bucket_summaries[:20]:
        print(
            f"- bucket={bucket_titles.get(loose_bucket, loose_bucket)} "
            f"rows={row_count} distinct_project_keys={key_count}"
        )
    print(f"csv: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
