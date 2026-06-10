from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from uuid import UUID


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _normalized_bid_parts(entry: dict[str, Any]) -> tuple[str, str]:
    bid_no = str(entry.get("source_bid_no") or "").strip().upper()
    bid_ord_raw = str(entry.get("source_bid_ord") or "000").strip() or "000"
    bid_ord_digits = "".join(ch for ch in bid_ord_raw if ch.isdigit())
    bid_ord = bid_ord_digits.zfill(3)[-3:] if bid_ord_digits else "000"
    return bid_no, bid_ord


def entry_has_cached_synap_url(entry: dict[str, Any], cache: dict[str, Any]) -> bool:
    bid_no, bid_ord = _normalized_bid_parts(entry)
    if not bid_no:
        return False
    prefix = f"{bid_no}|{bid_ord}|"
    for key, value in cache.items():
        cached_url = str(value or "").strip()
        if str(key).startswith(prefix) and "SynapDocViewServer/viewer/doc.html" in cached_url:
            return True
    return False


def select_uncached_entries(rows: list[dict[str, Any]], cache: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        entry_id = str(row.get("id") or "").strip()
        if not entry_id or entry_id in seen:
            continue
        seen.add(entry_id)
        if entry_has_cached_synap_url(row, cache):
            continue
        selected.append(row)
    return selected


def _read_cache(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): str(value) for key, value in payload.items() if str(value or "").strip()}


def _list_tracker_entries(*, page_size: int) -> list[dict[str, Any]]:
    from backend.repositories.factory import get_tracker_entry_repository
    from backend.repositories.factory import reset_tracker_entry_repository

    reset_tracker_entry_repository()
    repository = get_tracker_entry_repository()
    rows: list[dict[str, Any]] = []
    page = 1
    while True:
        batch, _total = repository.list_entries(
            page=page,
            page_size=page_size,
            q="",
            region="",
            notice_year="",
            exclude_auxiliary_titles=False,
            edited_only=False,
            source_run_id=None,
            source_tracker_run_id=None,
            sheet_name="",
            section_name="",
        )
        if not batch:
            break
        rows.extend(dict(item) for item in batch)
        if len(batch) < page_size:
            break
        page += 1
    return rows


def _warm_entry(entry_id: str) -> dict[str, Any]:
    from backend.api.routers.tracker_read_handlers import warm_tracker_entry_notice_file

    return warm_tracker_entry_notice_file(UUID(entry_id))


def build_notice_viewer_cache(
    *,
    local_sqlite_path: Path,
    cache_path: Path,
    limit: int,
    page_size: int,
    sleep_seconds: float,
    include_cached: bool,
    dry_run: bool,
) -> dict[str, Any]:
    os.environ["TRACKER_REPOSITORY_BACKEND"] = "sqlite"
    os.environ["LOCAL_SQLITE_PATH"] = str(local_sqlite_path)
    os.environ["NOTICE_VIEWER_CACHE_PATH"] = str(cache_path)

    rows = _list_tracker_entries(page_size=page_size)
    initial_cache = _read_cache(cache_path)
    candidates = rows if include_cached else select_uncached_entries(rows, initial_cache)
    if limit > 0:
        candidates = candidates[:limit]

    summary = {
        "total_entries": len(rows),
        "initial_cached_entries": len(rows) - len(select_uncached_entries(rows, initial_cache)),
        "candidate_entries": len(candidates),
        "ready": 0,
        "failed": 0,
        "skipped": 0,
        "dry_run": dry_run,
    }
    print(json.dumps({"event": "start", **summary}, ensure_ascii=False), flush=True)

    for index, entry in enumerate(candidates, start=1):
        entry_id = str(entry.get("id") or "").strip()
        bid_no, bid_ord = _normalized_bid_parts(entry)
        if not entry_id:
            summary["skipped"] += 1
            continue
        if dry_run:
            print(
                json.dumps(
                    {"event": "candidate", "index": index, "entry_id": entry_id, "bid_no": bid_no, "bid_ord": bid_ord},
                    ensure_ascii=False,
                ),
                flush=True,
            )
            continue
        started_at = time.monotonic()
        result = _warm_entry(entry_id)
        elapsed = round(time.monotonic() - started_at, 3)
        viewer_url = str(result.get("url") or "").strip()
        is_ready = bool(result.get("ready")) and "SynapDocViewServer/viewer/doc.html" in viewer_url
        if is_ready:
            summary["ready"] += 1
        else:
            summary["failed"] += 1
        print(
            json.dumps(
                {
                    "event": "warm",
                    "index": index,
                    "entry_id": entry_id,
                    "bid_no": bid_no,
                    "bid_ord": bid_ord,
                    "ready": is_ready,
                    "elapsed_sec": elapsed,
                    "url": viewer_url,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    final_cache = _read_cache(cache_path)
    summary["final_cache_keys"] = len(final_cache)
    print(json.dumps({"event": "complete", **summary}, ensure_ascii=False), flush=True)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build local Synap notice viewer cache for tracker entries.")
    parser.add_argument("--local-sqlite-path", type=Path, default=ROOT / "dist" / "notice-winner" / "data" / "local.sqlite3")
    parser.add_argument("--cache-path", type=Path, default=ROOT / "dist" / "notice-winner" / "data" / "notice_viewer_cache.json")
    parser.add_argument("--limit", type=int, default=0, help="Maximum entries to warm. 0 means all candidates.")
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--sleep-seconds", type=float, default=0.1)
    parser.add_argument("--include-cached", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    build_notice_viewer_cache(
        local_sqlite_path=args.local_sqlite_path,
        cache_path=args.cache_path,
        limit=max(int(args.limit or 0), 0),
        page_size=max(int(args.page_size or 200), 1),
        sleep_seconds=max(float(args.sleep_seconds or 0), 0.0),
        include_cached=bool(args.include_cached),
        dry_run=bool(args.dry_run),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
